from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union

#Type hinting, formula can be any of these
Formula = Union["Predicate", "And", "Or", "Not", "Implies", "ForAll", "Exists"]


#Predicate represents the atomic formulas such as P(x), Q(a, b), etc.
@dataclass (frozen=True)
class Predicate:
    name: str            #name of the predicate e.g. P, Q, R, etc.
    args: tuple[str, ...] = () #tuple of arguments e.g. [x, y, z]

    def __post_init__(self):
        object.__setattr__(self, "args", tuple(self.args))

    def __repr__(self):
        # If predicate has arguments → print P(x, y)
        if self.args:
            return f"{self.name}({', '.join(self.args)})"
        return self.name  #otherwise just print the name
        


#Represent AND conjunction(A /\ B)
@dataclass(frozen=True)
class And:
    #left and right subformulas
    left: Formula
    right: Formula

    def __repr__(self):
        return f"({self.left} and {self.right})"


        
#Not / negation       
@dataclass(frozen=True)
class Not:
    sub: Formula   #The formula being negated

    def __repr__(self):
        return f"not {self.sub}"
    


#Or / disjuction  
@dataclass(frozen=True)     
class Or:
    left: Formula
    right: Formula

    def __repr__(self):
        return f"({self.left} or {self.right})"


#Implies ->
@dataclass(frozen=True)
class Implies:
    left: Formula
    right: Formula

    def __repr__(self):
        return f"({self.left} -> {self.right})"



#For all: represents universal quantifier (∀x A)
@dataclass(frozen=True)   
class ForAll:
    var: str        #Quantified varuable (e.g. x)
    sub: Formula    #Formula inside the quantifier

    def __repr__(self):
        return f"forall {self.var} {self.sub}"        



#There exists (∃x A)
@dataclass(frozen=True)
class Exists:
    var: str        #Quantified varuable (e.g. x)
    sub: Formula    #Formula inside the quantifie

    def __repr__(self):
        return f"exists {self.var} {self.sub}"        

        

        
        
