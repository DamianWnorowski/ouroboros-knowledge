# omni_pipeline_stress_test

Source: gemini

MCP issues detected. Run /mcp list for status.Here is the stress-test analysis of the adaptive UCB1 LLM routing pipeline, heavily contextualized by the specific mathematical implementations found in your `src/adaptive.py` engine.

### Scenario 1: What breaks when 3 providers go down?
**The "Exploration Bleed" and the "Adaptive Doom Loop"**

In standard UCB1, the score is `avg_reward + sqrt(2 * ln(total_picks) / provider_picks)`. When 3 providers go down:
1. **The Initial Drop:** Their `avg_reward` quickly plummets as they return connection errors or timeouts (recording negative rewards). The router correctly shifts traffic to the surviving 6 providers.
2. **The Exploration Bleed:** As the 6 healthy providers continually serve requests, `total_picks` continually increases. Mathematically, the numerator `ln(total_picks)` grows while the denominator `provider_picks` for the dead providers remains stagnant. This causes their UCB1 exploration bonus to slowly but infinitely inflate. Periodically, the math forces the system to send requests to the dead providers just to "check if they are back up," guaranteeing persistent, periodic latency spikes and error cascades.
3. **The Adaptive Doom Loop (Specific to your engine):** `src/adaptive.py` monitors reward variance via `get_explore_rate()`. If the 6 surviving providers perform identically well, the variance of average rewards across the active pool drops below your `< 0.01` threshold. The system interprets this stability as "stagnation" and aggressively spikes the chaotic `explore_rate` up to **60%**. The router will begin violently throwing traffic at the 3 dead providers, effectively turning a stable 6-provider cluster into a self-DDOSing failure state in the name of exploration.

### Scenario 2: What if the learner converges on a suboptimal provider?
**"Softmax Lock-in" vs. "The Chaos Rescue"**

If a mediocre provider gets a lucky streak of easy prompts early on, and the optimal provider fails a few complex prompts, the system can converge on the suboptimal choice. 
1. **Softmax Lock-in:** While standard UCB1 mathematically guarantees all arms are pulled infinitely often (eventually correcting the mistake), `adaptive.py` applies a Softmax to the scores: `exp(min(s - max_score, 10))`. If the suboptimal provider establishes a solid lead in `avg_reward`, the exponentiation crushes the probability of the optimal provider being selected. The UCB1 exploration bonus `ln(total_picks)` grows logarithmically—which is very slow. The Softmax effectively locks the optimal provider out of receiving the pulls it needs to prove its superiority.
2. **The Variance Trap:** The system relies on low variance to trigger higher exploration. But if the suboptimal provider consistently succeeds (high score) while the starved optimal provider sits on an early, uncorrected failure (low score), the variance remains *high*. The system thinks it's perfectly healthy and keeps the baseline `explore_rate` low.
3. **The Chaos Rescue:** The only thing that breaks this lock-in is your logistic map chaos bypass (`pick._chaos_state = 3.99 * ...`). It forces purely random selection outside the UCB1 bounds. The system relies entirely on this chaotic baseline hitting the optimal provider enough times by pure chance to drag its `avg_reward` back into a competitive range, at which point the UCB1 math can take over again. 

### How to Fix the Architecture
To harden this pipeline, you need to decouple *availability* from *capability*:
* **Implement Circuit Breakers:** If a provider fails $N$ times consecutively, temporarily remove it from the `candidates` pool (or set its UCB1 score to negative infinity) for a cooldown period. Do not let `ln(total_picks)` revive dead infrastructure.
* **Decay Historical Rewards:** UCB1 assumes a stationary environment. LLM providers degrade, update, and change. Implement an exponential moving average (EMA) for rewards instead of absolute totals, ensuring early lucky streaks or ancient failures "age out" of the routing logic.