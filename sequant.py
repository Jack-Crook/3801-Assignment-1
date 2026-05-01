from __future__ import annotations
from AST import Formula
from dataclasses import dataclass

@dataclass(frozen = True)
class Sequant:
    left: tuple[Formula, ...] = ()  # Γ (assumptions)
    right: tuple[Formula, ...] = ()    # Δ (goals)

    def __post_init__(self):
        object.__setattr__(self, "left", tuple[Formula, ...](self.left))
        object.__setattr__(self, "right", tuple[Formula, ...](self.right))


    def __repr__(self):
        left_str = ", ".join(str(f) for f in self.left) if self.left else "∅"
        right_str = ", ".join(str(f) for f in self.right) if self.right else "∅"
        return f"{left_str} ⊢ {right_str}"