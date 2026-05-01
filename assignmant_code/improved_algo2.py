from __future__ import annotations
from dataclasses import dataclass
from AST import *
from sequant import Sequant

fresh_counter = 0


def fresh_term():
    global fresh_counter
    fresh_counter += 1
    return f"c{fresh_counter}"


def substitute(formula, var, term):
    if isinstance(formula, Predicate):
        new_args = tuple(term if a == var else a for a in formula.args)
        return Predicate(formula.name, new_args)

    if isinstance(formula, And):
        return And(
            substitute(formula.left, var, term),
            substitute(formula.right, var, term)
        )

    if isinstance(formula, Or):
        return Or(
            substitute(formula.left, var, term),
            substitute(formula.right, var, term)
        )

    if isinstance(formula, Not):
        return Not(substitute(formula.sub, var, term))

    if isinstance(formula, Implies):
        return Implies(
            substitute(formula.left, var, term),
            substitute(formula.right, var, term)
        )

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
    terms = set()

    if isinstance(formula, Predicate):
        for a in formula.args:
            terms.add(a)

    elif isinstance(formula, Not):
        terms |= collect_terms(formula.sub)

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


def normalize_sequant(sequant):
    left = tuple(sorted(sequant.left, key=repr))
    right = tuple(sorted(sequant.right, key=repr))
    return Sequant(left, right)


def sequant_key(sequant):
    s = normalize_sequant(sequant)
    return (tuple(map(repr, s.left)), tuple(map(repr, s.right)))


def formula_size(formula):
    if isinstance(formula, Predicate):
        return 1
    if isinstance(formula, Not):
        return 1 + formula_size(formula.sub)
    if isinstance(formula, (And, Or, Implies)):
        return 1 + formula_size(formula.left) + formula_size(formula.right)
    if isinstance(formula, (ForAll, Exists)):
        return 1 + formula_size(formula.sub)
    return 1


def sequent_score(sequant):
    total = 0
    for f in sequant.left + sequant.right:
        total += formula_size(f)
    return total


@dataclass
class Stats:
    nodes_expanded: int = 0
    branches_created: int = 0
    quantifier_steps: int = 0
    max_depth: int = 0


def apply_and_left(sequant):
    for i, f in enumerate(sequant.left):
        if isinstance(f, And):
            new_left = sequant.left[:i] + (f.left, f.right) + sequant.left[i+1:]
            return [Sequant(new_left, sequant.right)]
    return None


def apply_or_right(sequant):
    for i, f in enumerate(sequant.right):
        if isinstance(f, Or):
            new_right = sequant.right[:i] + (f.left, f.right) + sequant.right[i+1:]
            return [Sequant(sequant.left, new_right)]
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


def apply_forall_right(sequant, stats):
    for i, f in enumerate(sequant.right):
        if isinstance(f, ForAll):
            c = fresh_term()
            inst = substitute(f.sub, f.var, c)
            new_right = sequant.right[:i] + (inst,) + sequant.right[i+1:]
            stats.quantifier_steps += 1
            return [Sequant(sequant.left, new_right)]
    return None


def apply_exists_left(sequant, stats):
    for i, f in enumerate(sequant.left):
        if isinstance(f, Exists):
            c = fresh_term()
            inst = substitute(f.sub, f.var, c)
            new_left = sequant.left[:i] + (inst,) + sequant.left[i+1:]
            stats.quantifier_steps += 1
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


def apply_implies_left(sequant):
    for i, f in enumerate(sequant.left):
        if isinstance(f, Implies):
            s1 = Sequant(sequant.left[:i] + sequant.left[i+1:], sequant.right + (f.left,))
            s2 = Sequant(sequant.left[:i] + (f.right,) + sequant.left[i+1:], sequant.right)
            return [s1, s2]
    return None


def apply_forall_left(sequant, instantiation_history, stats):
    for i, f in enumerate(sequant.left):
        if isinstance(f, ForAll):
            formula_id = ("L", i, repr(f))
            used_terms = instantiation_history.setdefault(formula_id, set())

            candidate_terms = sorted(terms_in_sequant(sequant))
            for t in candidate_terms:
                if t not in used_terms:
                    used_terms.add(t)
                    inst = substitute(f.sub, f.var, t)
                    new_left = sequant.left[:i] + (inst,) + sequant.left[i+1:]
                    stats.quantifier_steps += 1
                    return [Sequant(new_left, sequant.right)]

            fresh = fresh_term()
            used_terms.add(fresh)
            inst = substitute(f.sub, f.var, fresh)
            new_left = sequant.left[:i] + (inst,) + sequant.left[i+1:]
            stats.quantifier_steps += 1
            return [Sequant(new_left, sequant.right)]
    return None


def apply_exists_right(sequant, instantiation_history, stats):
    for i, f in enumerate(sequant.right):
        if isinstance(f, Exists):
            formula_id = ("R", i, repr(f))
            used_terms = instantiation_history.setdefault(formula_id, set())

            candidate_terms = sorted(terms_in_sequant(sequant))
            for t in candidate_terms:
                if t not in used_terms:
                    used_terms.add(t)
                    inst = substitute(f.sub, f.var, t)
                    new_right = sequant.right[:i] + (inst,) + sequant.right[i+1:]
                    stats.quantifier_steps += 1
                    return [Sequant(sequant.left, new_right)]

            fresh = fresh_term()
            used_terms.add(fresh)
            inst = substitute(f.sub, f.var, fresh)
            new_right = sequant.right[:i] + (inst,) + sequant.right[i+1:]
            stats.quantifier_steps += 1
            return [Sequant(sequant.left, new_right)]
    return None


def expand_improved(sequant, instantiation_history, stats):
    if is_closed(sequant):
        return []

    # Priority 1: non-branching propositional rules
    for rule in [apply_and_left, apply_or_right, apply_implies_right, apply_not_left, apply_not_right]:
        result = rule(sequant)
        if result is not None:
            return result

    # Priority 2: deterministic quantifier rules
    result = apply_forall_right(sequant, stats)
    if result is not None:
        return result

    result = apply_exists_left(sequant, stats)
    if result is not None:
        return result

    # Priority 3: branching propositional rules
    for rule in [apply_and_right, apply_or_left, apply_implies_left]:
        result = rule(sequant)
        if result is not None:
            stats.branches_created += 1
            return sorted(result, key=sequent_score)

    # Priority 4: controlled instantiation
    result = apply_forall_left(sequant, instantiation_history, stats)
    if result is not None:
        return result

    result = apply_exists_right(sequant, instantiation_history, stats)
    if result is not None:
        return result

    return None


def prove_improved(sequant, seen=None, instantiation_history=None, depth=0, max_depth=100, stats=None):
    if seen is None:
        seen = set()
    if instantiation_history is None:
        instantiation_history = {}
    if stats is None:
        stats = Stats()

    stats.nodes_expanded += 1
    stats.max_depth = max(stats.max_depth, depth)

    sequant = normalize_sequant(sequant)

    if is_closed(sequant):
        return True, stats

    if depth > max_depth:
        return False, stats

    key = sequant_key(sequant)
    if key in seen:
        return False, stats

    seen = seen | {key}

    children = expand_improved(sequant, instantiation_history, stats)

    if children is None:
        return False, stats

    if children == []:
        return True, stats

    for child in children:
        ok, stats = prove_improved(
            child,
            seen=seen,
            instantiation_history=instantiation_history,
            depth=depth + 1,
            max_depth=max_depth,
            stats=stats
        )
        if not ok:
            return False, stats

    return True, stats