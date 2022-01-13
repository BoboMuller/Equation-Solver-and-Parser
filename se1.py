"""
>>> ParseAExpr().parse("exp(x) + 2*y")
[(Plus(Exp(Var('x')), Times(Con(2), Var('y'))), '')]
"""

from pcomb import *
from bool import *
import math
import z3

"""
<expr> ::= <term> + <expr> | <term>
<term> ::= <factor> * <term> | <factor>
<factor> ::= <expon>
<expon> ::= exp( <atom> ) | <atom>
<atom> ::= <con> | <var> | ( <expr> )
"""

class ParseAExpr(Parser):
    def __init__(self):
        self.parser = ParsePlus() ^ ParseTerm()

class ParseTerm(Parser):
    def __init__(self):
        self.parser = ParseTimes() ^ ParseFactor()

class ParseFactor(Parser):
    def __init__(self):
        self.parser = ParseCon() ^ ParseVar() ^ ParseParen()

class ParseCon(Parser):
    def __init__(self):
        self.parser = ParseInt() >> (lambda n:
                      Return(Con(n)))

class ParseVar(Parser):
    def __init__(self):
        self.parser = ParseIdent() >> (lambda name:
                      Return(Var(name)))

class ParseParen(Parser):
    def __init__(self):
        self.parser = ParseSymbol('(') >> (lambda _:
                                           ParseAExpr() >> (lambda e:
                      ParseSymbol(')') >> (lambda _:
                      Return(e))))

class ParsePlus(Parser):
    def __init__(self):
        self.parser = ParseTerm()      >> (lambda t:
                      ParseSymbol('+') >> (lambda _:
                                           ParseAExpr() >> (lambda e:
                      Return(Plus(t, e)))))

class ParseTimes(Parser):
    def __init__(self):
        self.parser = ParseFactor()    >> (lambda x:
                      ParseSymbol('*') >> (lambda _:
                      ParseTerm()      >> (lambda y:
                      Return(Times(x, y)))))


class Expr:
    def __add__(self, other):
        return Plus(self, other)

    def __mul__(self, other):
        return Times(self, other)

    def toZ3(self):
        return "Implement on a level below"


class Con(Expr):
    def __init__(self, val):
        self.val = val
        
    def __str__(self):
        return str(self.val) # f"Con({self.val})"

    def ev(self, env):
        return self.val

    def toZ3(self):
        return self.val


class Var(Expr):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name # f"Var({self.name})"

    def ev(self, env):
        if self.name[0] == '-':
            return -env[self.name[1:]]
        return env[self.name]

    def toZ3(self):
        return z3.Int(self.name)


class BinOp(Expr):
    def __init__(self, left, right):
        self.left  = left
        self.right = right

    def __str__(self):
        return f"({self.left} {self.op} {self.right})" # f"{self.name}({self.left}, {self.right})" # +

    def ev(self, env):
        return self.fun(self.left.ev(env), self.right.ev(env))


class Plus(BinOp):
    name = "Plus"
    fun  = lambda _, x, y: x + y
    op   = '+'

    def toZ3(self):
        return  self.left.toZ3() + self.right.toZ3()

class Times(BinOp):
    name = "Times"
    fun  = lambda _, x, y: x * y
    op   = '*'

    def toZ3(self):
        return self.left.toZ3() * self.right.toZ3()


