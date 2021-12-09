"""
<bool> ::= <disj> or <bool> | <disj>
<disj> ::= <conj> and <disj> | <conj>
<conj> ::= <var> | ( <bool> )

P or (Q and R or P)
"""

from pcomb import *
from se1 import *


class ParseExpr(Parser):
    def __init__(self):
        self.parser = ParseBExpr() ^ ParseAExpr()


class ParseBExpr(Parser):
    def __init__(self):
        self.parser = ParseOr() ^ ParseDisj()


class ParseDisj(Parser):
    def __init__(self):
        self.parser = ParseAnd() ^ ParseConj()


class ParseConj(Parser):
    def __init__(self):
        self.parser = ParseCmp() ^ ParseBParen()


class ParseCmp(Parser):
    def __init__(self):
        self.parser = ParseAExpr() >> (lambda l:
                        (ParseSymbol("=") ^ ParseSymbol("<")) >> (lambda cmp:
                                                                  ParseAExpr() >> (lambda r:
                        Return(Less(l, r)) if cmp == "<" else Return(Equal(l, r)))))


class ParseBVar(Parser):
    def __init__(self):
        self.parser = ParseIdentifier() >> (lambda name:
                      Return(BVar(name)))


class ParseBParen(Parser):
    def __init__(self):
        self.parser = ParseSymbol("(") >> (lambda _:
                      ParseBExpr()     >> (lambda e:
                      ParseSymbol(")") >> (lambda _:
                      Return(e))))

class ParseOr(Parser):
    def __init__(self):
        self.parser = ParseDisj() >> (lambda d:
                      ParseSymbol("or") >> (lambda _:
                      ParseBExpr() >> (lambda e:
                      Return(Or(d, e)))))

class ParseAnd(Parser):
    def __init__(self):
        self.parser = ParseConj() >> (lambda x:
                      ParseSymbol("and") >> (lambda _:
                      ParseDisj() >> (lambda y:
                      Return(And(x, y)))))

class BExpr:
    pass

class BVar(BExpr):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def ev(self, env):
        return env[self.name]

class Op2(BExpr):
    def __init__(self, left, right):
        self.left  = left
        self.right = right

    def __str__(self):
        return f"({self.left} {self.op} {self.right})"

    def ev(self, env):
        return self.fun(self.left.ev(env), self.right.ev(env))
    
class Or(Op2):
    op = "or"
    fun = lambda _, x, y: x or y

    def toZ3(self):
        return z3.Or(self.left.toZ3(), self.right.toZ3())


class And(Op2):
    op = "and"
    fun = lambda _, x, y: x and y

    def toZ3(self):
        return z3.And(self.left.toZ3(), self.right.toZ3())
    
class Less(Op2):
    op = "<"
    fun = lambda _, x, y: x < y

    def toZ3(self):
        return  self.left.toZ3() < self.right.toZ3()

class Equal(Op2):
    op = "="
    fun = lambda _, x, y: x == y

    def toZ3(self):
        return  self.left.toZ3() == self.right.toZ3()