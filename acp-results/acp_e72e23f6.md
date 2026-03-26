I have rebalanced the phase scheduling weights and implemented the requested diversity enforcement mechanism in `autonomous_brain.py`.

Here is a summary of the changes:
1. **Priority Adjustments**: 
   - Reduced `necromancer` base priority from `9` to `4`.
   - Boosted `oracle` from `7` to `9`.
   - Boosted `swarm` from `6` to `8`.
   - Boosted `immunize` from `5` to `8`.
2. **Diversity Enforcement**: 
   - Added a `phase_history` tracker to the `BrainState` to remember the last 100 phases executed, persisting across state loads and saves.
   - Updated `compute_phase_priority` to evaluate the last 50 phases; if a phase has executed more than 40% of the time, its priority is dropped to `-100`, effectively blocking it from running and forcing the system to pick diverse alternative phases.