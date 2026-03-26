import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Any

# Domain definitions for the 9x9 Synergy Coupling Matrix
DOMAINS = ["AGI", "QC", "NM", "BCI", "CLI", "NANO", "WBE", "SPACE", "BIO"]
DOMAIN_IDX = {domain: idx for idx, domain in enumerate(DOMAINS)}

def _build_synergy_matrix() -> np.ndarray:
    """Constructs the 9x9 synergy coupling matrix with specific values."""
    matrix = np.full((9, 9), 0.3)
    np.fill_diagonal(matrix, 1.0)
    
    couplings = [
        ("AGI", "WBE", 0.95),
        ("AGI", "NANO", 0.88),
        ("NANO", "WBE", 0.98),
        ("AGI", "QC", 0.85),
        ("AGI", "NM", 0.80),
        ("QC", "NM", 0.75),
        ("BCI", "WBE", 0.90),
        ("NANO", "BIO", 0.85),
        ("SPACE", "NANO", 0.70),
        ("CLI", "AGI", 0.60)
    ]
    
    for d1, d2, val in couplings:
        i, j = DOMAIN_IDX[d1], DOMAIN_IDX[d2]
        matrix[i, j] = val
        matrix[j, i] = val
        
    return matrix

SYNERGY_MATRIX = _build_synergy_matrix()

def compute_eigenmode(matrix: np.ndarray) -> Tuple[float, np.ndarray]:
    """Returns the dominant eigenvalue and its corresponding eigenvector."""
    eigenvalues, eigenvectors = np.linalg.eigh(matrix)
    max_idx = np.argmax(eigenvalues)
    return float(eigenvalues[max_idx]), eigenvectors[:, max_idx]

def synergy_score(domain_a: str, domain_b: str) -> float:
    """Returns the coupling strength between two domains."""
    if domain_a not in DOMAIN_IDX or domain_b not in DOMAIN_IDX:
        raise ValueError(f"Invalid domains. Must be one of {DOMAINS}")
    return float(SYNERGY_MATRIX[DOMAIN_IDX[domain_a], DOMAIN_IDX[domain_b]])

def critical_gates(year: int) -> List[str]:
    """Returns the list of gate decisions for a given year."""
    gates_timeline = {
        2025: ["QC Error Correction Threshold", "NM Hardware Viability Phase 1"],
        2028: ["AGI Proto-Coherence", "BCI Read/Write Broad Adoption"],
        2032: ["NANO Assembly Alpha", "WBE Sub-System Mapping"],
        2035: ["AGI-WBE Integration", "SPACE Orbital Manufacturing Base"],
        2040: ["Full WBE Emulation", "NANO-AGI Singularity Interface"]
    }
    return gates_timeline.get(year, ["Continuous System Evolution"])

def reverse_provenance(target_state: str) -> List[str]:
    """Traces prerequisites backward for a given target state."""
    provenance_map = {
        "WBE": ["High-Res Brain Mapping", "AGI Pattern Recognition", "Exascale Compute"],
        "NANO": ["Protein Folding Mastery", "Quantum Chemistry Simulation", "AGI Design"],
        "AGI": ["Neuromorphic Scaling", "Algorithmic Efficiency", "Unsupervised World Models"],
        "SPACE": ["Advanced Propulsion", "Closed Loop Life Support", "NANO Materials"]
    }
    # Default fallback traces generic systems prerequisites
    return provenance_map.get(target_state.upper(), ["Foundational Research", "Compute Scaling", "Energy Abundance"])

def eternal_patterns_analysis(system_description: str) -> Dict[str, str]:
    """Applies the 10-lens eternal patterns analysis to a system description."""
    lenses = [
        "Spiral", "Labyrinth", "Eye", "Pillar", "Serpent", 
        "Gate", "Scale", "Flame", "Fourfold Circle", "Unfinished Stone"
    ]
    
    # In a full engine, this would use LLM or complex heuristics.
    # Here we mock the generative analytical mappings.
    return {
        lens: f"[{lens.upper()} LENS]: Evaluating '{system_description}' reveals recursive structural alignment with {lens.lower()} dynamics."
        for lens in lenses
    }

@dataclass
class PolynestedConfig:
    """Preset configuration dataclass for the polynested fracture engine."""
    name: str = "polynested"
    matrix: np.ndarray = field(default_factory=lambda: SYNERGY_MATRIX)
    domains: List[str] = field(default_factory=lambda: DOMAINS)
    dimension: int = len(DOMAINS)
    
    def get_context(self) -> Dict[str, Any]:
        eigenval, eigenvec = compute_eigenmode(self.matrix)
        return {
            "eigenvalue": eigenval,
            "eigenvector": eigenvec.tolist(),
            "domains": self.domains
        }

# Register the preset for the fracture engine
PRESETS = {}
PRESETS['polynested'] = {
    'config': PolynestedConfig(),
    'matrix': SYNERGY_MATRIX,
    'functions': {
        'compute_eigenmode': compute_eigenmode,
        'synergy_score': synergy_score,
        'critical_gates': critical_gates,
        'reverse_provenance': reverse_provenance,
        'eternal_patterns_analysis': eternal_patterns_analysis
    }
}
