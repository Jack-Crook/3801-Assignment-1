from AST import *

#reads formulas from text file (1 per line)
def read_formulas(filename):
    with open(filename, "r") as f:
        return [line.strip() for line in f if line.strip()] #strip() removes white space and ignores empty lines



#converts string into list of tokens
def tokenize(s):
    #adds spaces around special symbols so they become seperate tokens
    s = s.replace('(', ' ( ').replace(')', ' ) ')
    s = s.replace(',', ' , ')
    s = s.replace('->', ' -> ')
    return s.split()    #split into list of tokens



def parse_formula(tokens):
    return parse_implies(tokens)

def parse_implies(tokens):
    left = parse_or(tokens)
    if tokens and tokens[0] in {"->", "implies"}:
        op = tokens.pop(0)
        right = parse_implies(tokens)
        left = Implies(left, right)
    return left

def parse_or(tokens):
    left = parse_and(tokens)
    while tokens and tokens[0] == "or":
        tokens.pop(0)
        right = parse_and(tokens)
        left = Or(left, right)
    return left

def parse_and(tokens):
    left = parse_unary(tokens)
    while tokens and tokens[0] == "and":
        tokens.pop(0)
        right = parse_unary(tokens)
        left = And(left, right)
    return left

def parse_unary(tokens):
    if not tokens:
        raise ValueError("Expected token, got nothing")
    if tokens[0] == "not":
        tokens.pop(0)
        return Not(parse_unary(tokens))
    if tokens[0] == "forall":
        tokens.pop(0)
        if not tokens:
            raise SyntaxError("Expected variable after forall")
        var = tokens.pop(0)
        return ForAll(var, parse_unary(tokens))
    if tokens[0] == "exists":
        tokens.pop(0)
        if not tokens:
            raise SyntaxError("Expected variable after exists")
        var = tokens.pop(0)
        return Exists(var, parse_unary(tokens))
    return parse_atom(tokens)

def parse_atom(tokens):
    if not tokens:
        raise ValueError("Expected token, got nothing")

    if tokens[0] == "(":
        tokens.pop(0)
        sub = parse_formula(tokens)
        if not tokens or tokens.pop(0) != ")":
            raise SyntaxError("Expected )")
        return sub

    name = tokens.pop(0)
    if tokens and tokens[0] == "(":
        tokens.pop(0)
        args = []
        while tokens and tokens[0] != ")":
            args.append(tokens.pop(0))
            if tokens and tokens[0] == ",":
                tokens.pop(0)
        if not tokens:
            raise SyntaxError("Expected ) after arguments")
        tokens.pop(0)
        return Predicate(name, tuple(args))

    return Predicate(name, ())
        
            
formulas = read_formulas("formulas.txt")

for f in formulas:
    try:
        tokens = tokenize(f)
        ast = parse_formula(tokens)

        if tokens:
            raise SyntaxError(f"Leftover tokens: {tokens}")

        print(f"OK   : {f}")
        print(f"AST  : {ast}")
        print()

    except Exception as e:
        print(f"FAIL : {f}")
        print(f"ERR  : {e}")
        print()