from dataclasses import dataclass, field
from AST import *
from sequant import Sequant


fresh_counter = 0

def fresh_term():
    global fresh_counter
    fresh_counter +=1
    return f"c{fresh_counter}"


def substitute(formula, var, term):

    if isinstance(formula, Predicate):
        new_args = tuple(term if a == var else a for a in formula.args)
        return Predicate(formula.name, new_args)


    if isinstance(formula, And):
        return And(
            substitute(formula.left, var, term), 
            substitute(formula.right, var, term))

    if isinstance(formula, Or):
        return Or(substitute(formula.left, var, term),
                   substitute(formula.right, var, term))


    if isinstance(formula, Not):
        return Not(substitute(formula.sub, var, term))


    if isinstance(formula, Implies):
            return Implies(substitute(formula.left, var, term), 
                           substitute(formula.right, var, term))


    if isinstance(formula, ForAll):
        if formula.var == var:
            return formula
        return ForAll(formula.var, substitute(formula.sub, var, term))

    if isinstance(formula, Exists):
        if formula.var == var:
            return formula
        return Exists(formula.var, substitute(formula.sub, var, term))

    return formula

def is_closed(sequant):
    for f in sequant.left:
        if f in sequant.right:
            return True
    return False


def collect_terms(formula):
    terms  = set()
    if isinstance(formula, Predicate):
        for a in formula.args:
            terms.add(a)
    
    elif isinstance(formula, Not):
        terms|=collect_terms(formula.sub)

    elif isinstance(formula, (And, Or, Implies)):
        terms |= collect_terms(formula.left)
        terms |= collect_terms(formula.right)

    elif isinstance(formula, (ForAll, Exists)):
        terms |= collect_terms(formula.sub)
    return terms

def terms_in_sequant(sequant):
    terms = set()
    for f in sequant.left + sequant.right:
        terms |= collect_terms(f)
    return terms


def apply_and_left(sequant):
    for i, f in enumerate(sequant.left):
        if isinstance(f, And):
            new_left = sequant.left[:i] + (f.left, f.right) + sequant.left[i+1:]
            return [Sequant(new_left, sequant.right)]
    return None

def apply_and_right(sequant):
    for i, f in enumerate(sequant.right):
        if isinstance(f, And):
            s1 = Sequant(sequant.left, sequant.right[:i] + (f.left,) + sequant.right[i+1:])
            s2 = Sequant(sequant.left, sequant.right[:i] + (f.right,) + sequant.right[i+1:])
            return [s1, s2]
    return None


def apply_or_left(sequant):
    for i, f in enumerate(sequant.left):
        if isinstance(f, Or):
            s1 = Sequant(sequant.left[:i] + (f.left,) + sequant.left[i+1:], sequant.right)
            s2 = Sequant(sequant.left[:i] + (f.right,) + sequant.left[i+1:], sequant.right)
            return [s1, s2]
    return None

def apply_or_right(sequant):
    for i, f in enumerate(sequant.right):
        if isinstance(f, Or):
            new_right = sequant.right[:i] + (f.left, f.right) + sequant.right[i+1:]
            return [Sequant(sequant.left, new_right)]
    return None

def apply_implies_left(sequant):
    for i, f in enumerate(sequant.left):
        if isinstance(f, Implies):
            s1 = Sequant(sequant.left[:i] + sequant.left[i+1:], sequant.right + (f.left,))
            s2 = Sequant(sequant.left[:i] + (f.right,) + sequant.left[i+1:], sequant.right)
            return [s1, s2]
    return None

def apply_implies_right(sequant):
    for i, f in enumerate(sequant.right):
        if isinstance(f, Implies):
            new_left = sequant.left + (f.left,)
            new_right = sequant.right[:i] + (f.right,) + sequant.right[i+1:]
            return [Sequant(new_left, new_right)]
    return None

def apply_not_left(sequant):
    for i, f in enumerate(sequant.left):
        if isinstance(f, Not):
            new_left = sequant.left[:i] + sequant.left[i+1:]
            new_right = sequant.right + (f.sub,)
            return [Sequant(new_left, new_right)]
    return None

def apply_not_right(sequant):
    for i, f in enumerate(sequant.right):
        if isinstance(f, Not):
            new_left = sequant.left + (f.sub,)
            new_right = sequant.right[:i] + sequant.right[i+1:]
            return [Sequant(new_left, new_right)]
    return None

def apply_forall_left(sequant):
    for i, f in enumerate(sequant.left):
        if isinstance(f, ForAll):
            terms = list(terms_in_sequant(sequant))
            if not terms:
                terms = [fresh_term()]
            out = []
            for t in terms:
                inst = substitute(f.sub, f.var, t)
                new_left = sequant.left[:i] + (inst,) + sequant.left[i+1:]
                out.append(Sequant(new_left, sequant.right))
            return out
    return None


def apply_forall_right(sequant):
    for i, f in enumerate(sequant.right):
        if isinstance(f, ForAll):
            c = fresh_term()
            inst = substitute(f.sub, f.var, c)
            new_right = sequant.right[:i] + (inst,) + sequant.right[i+1:]
            return [Sequant(sequant.left, new_right)]
    return None


def apply_exists_left(sequant):
    for i, f in enumerate(sequant.left):
        if isinstance(f, Exists):
            c = fresh_term()
            inst = substitute(f.sub, f.var, c)
            new_left = sequant.left[:i] + (inst,) + sequant.left[i+1:]
            return [Sequant(new_left, sequant.right)]
    return None

def apply_exists_right(sequant):
    for i, f in enumerate(sequant.right):
        if isinstance(f, Exists):
            terms = list(terms_in_sequant(sequant))
            if not terms:
                terms = [fresh_term()]
            out = []
            for t in terms:
                inst = substitute(f.sub, f.var, t)
                new_right = sequant.right[:i] + (inst,) + sequant.right[i+1:]
                out.append(Sequant(sequant.left, new_right))
            return out
    return None


def expand(sequant):
    if is_closed(sequant):
        return []

    rules = [
        apply_and_left,
        apply_and_right,
        apply_or_left,
        apply_or_right,
        apply_implies_left,
        apply_implies_right,
        apply_not_left,
        apply_not_right,
        apply_forall_left,
        apply_forall_right,
        apply_exists_left,
        apply_exists_right,
    ]

    for rule in rules:
        result = rule(sequant)
        if result is not None:
            return result

    return None

def sequant_key(sequant):
    return (tuple(sequant.left), tuple(sequant.right))
    

def prove(sequant, seen=None, depth=0, max_depth=100):
    if seen is None:
        seen = set()

    if is_closed(sequant):
        return True

    if depth > max_depth:
        return False

    key = sequant_key(sequant)
    if key in seen:
        return False

    seen = seen | {key}

    children = expand(sequant)

    if children is None:
        return False

    if children == []:
        return True

    for child in children:
        if not prove(child, seen, depth +1, max_depth):
            return False
        
    return True
