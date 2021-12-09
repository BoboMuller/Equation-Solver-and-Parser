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
        self.parser = ParseExpon()

class ParseExpon(Parser):
    def __init__(self):
        self.parser = ParseExp() ^ ParseAtom()
        
class ParseAtom(Parser):
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

class ParseExp(Parser):
    def __init__(self):
        self.parser = ParseSymbol("exp") >> (lambda _:
                      ParseAtom()        >> (lambda a:
                      Return(Exp(a))))


class Expr:
    def __add__(self, other):
        return Plus(self, other)

    def __mul__(self, other):
        return Times(self, other)

    def __truediv__(self, other):
        return Divide(self, other)

    def __sub__(self, other):
        return Minus(self, other)

    def diff(self, var):
        return "Error! diff not implemented"

    def toZ3(self):
        return "Implement on a level below"


class Con(Expr):
    def __init__(self, val):
        self.val = val
        
    def __str__(self):
        return str(self.val) # f"Con({self.val})"

    def __neg__(self):
        return Con(-self.val)

    def ev(self, env):
        return self.val

    def diff(self, var):
        return Con(0)

    def simplify(self):
        return self

    def __eq__(self, other):
        if type(other).__name__ != "Con":
            return False
        return self.val == other.val
    
    def vars_(self):
        return []

    def toZ3(self):
        return self.val


class Var(Expr):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name # f"Var({self.name})"

    def __neg__(self):
        if self.name[0] == '-':
            return Var(self.name[1:])
        else:
            return Var('-' + self.name)

    def ev(self, env):
        if self.name[0] == '-':
            return -env[self.name[1:]]
        return env[self.name]

    def diff(self, var):
        if self.name == var:
            return Con(1)
        elif self.name == '-'+var:
            return -Con(1)
        else:
            return Con(0)

    def simplify(self):
        return self

    def __eq__(self, other):
        if type(other).__name__ != "Var":
            return False
        return self.name == other.name

    def vars_(self):
        return [self.name]

    def toZ3(self):
        return z3.Int(self.name)


class BinOp(Expr):
    def __init__(self, left, right):
        self.left  = left
        self.right = right

    def __str__(self):
        return f"({self.left} {self.op} {self.right})" # f"{self.name}({self.left}, {self.right})" # +

    def __neg__(self):
        return self * -Con(1)

    def ev(self, env):
        return self.fun(self.left.ev(env), self.right.ev(env))

    def __eq__(self, other):
        if not isinstance(other, BinOp):
            return False
        return self.name == other.name and self.left == other.left and self.right == other.right

    def vars_(self):
        return list(set(self.left.vars_() + self.right.vars_()))
        #Liste zu set damit duplikate weg sind und wieder zu einer liste

    def toZ3(self):
        self.left.toZ3()
        self.right.toz3()


class Plus(BinOp):
    name = "Plus"
    fun  = lambda _, x, y: x + y
    op   = '+'

    def diff(self, var):
        return self.left.diff(var) + self.right.diff(var)

    def simplify(self):
        simple_left  = self.left.simplify()
        simple_right = self.right.simplify()

        vl  = None
        vr = None
        if simple_left.vars_() == []:
            vl = simple_left.ev({})
        if simple_right.vars_() == []:
            vr = simple_right.ev({})

        if vl != None and vr != None:
            return Con(vl + vr)
        if vl == 0:
            return simple_right
        elif vr == 0:
            return simple_left
        else:
            return simple_left + simple_right

    def toZ3(self):
        return  self.left.toZ3() + self.right.toZ3()


class Minus(BinOp):
    op = '-'
    fun = lambda _, x, y: x - y

    def diff(self, var):
        return self.left.diff(var) - self.right.diff(var)

    def simplify(self):
        simple_left = self.left.simplify()
        simple_right = self.right.simplify()
        ev_l = None
        ev_r = None

        if simple_left.vars_() == []:
            ev_l = simple_left.ev({})
        if simple_right.vars_() == []:
            ev_r = simple_right.ev({})
        if ev_l != None and ev_r != None:
            return Con(ev_l - ev_r)
        elif ev_l == 0:
            return Con(0) - simple_right
        elif ev_r == 0:
            return simple_left
        else:
            return simple_left - simple_right


class Times(BinOp):
    name = "Times"
    fun  = lambda _, x, y: x * y
    op   = '*'

    def diff(self, var):
        return self.left.diff(var) * self.right + self.left * self.right.diff(var)

    def simplify(self):
        simple_left  = self.left.simplify()
        simple_right = self.right.simplify()
        vl  = None
        vr = None
        if simple_left.vars_() == []:
            vl = simple_left.ev({})
        if simple_right.vars_() == []:
            vr = simple_right.ev({})

        if vl != None and vr != None:
            return Con(vl * vr)
        if vl == 0 or vr == 0:
            return Con(0)
        elif vl == 1:
            return simple_right
        elif vr == 1:
            return simple_left
        else:
            return simple_left * simple_right

    def toZ3(self):
        return self.left.toZ3() * self.right.toZ3()



class Divide(BinOp):
    op = '/'

    def fun(self, x, y):
        return x / y

    def diff(self, var):
        return (self.left.diff(var) * self.right - self.right.diff(var) * self.left) / (self.right * self.right)


    def simplify(self):
        simple_left = self.left.simplify()
        simple_right = self.right.simplify()
        ev_l = None
        ev_r = None


        if simple_left.vars_() == []:
            ev_l = simple_left.ev({})
        if simple_right.vars_() == []:
            ev_r = simple_right.ev({})

        if ev_l != None and ev_r != None:
            return Con(ev_l / ev_r)
        if ev_r == 1:
            return simple_left
        elif ev_r == 0:
            raise ZeroDivisionError
        elif ev_l == 0:
            return simple_right
        else:
            return simple_left / simple_right


class UnEx(Expr):
    def __init__(self, arg):
        self.arg = arg

    def __str__(self):
        return f"{self.op}({self.arg})" # f"Exp({self.arg})"

    def __neg__(self):
        self.arg = self.arg.__neg__()
        return self

    def __eq__(self, other):
        if not isinstance(other, Exp):
            return False
        return self.arg == other.arg

    def vars_(self):
        return self.arg.vars_()

    def ev(self, env):
        b = self.arg.ev(env)
        return self.fun(b)


class Exp(UnEx):

    op = 'Exp'

    def fun(self, inner):
        return math.exp(inner)

    def diff(self, var):
        return Exp(self.arg) * self.arg.diff(var)

    def simplify(self):
        simple_arg = self.arg.simplify()

        if simple_arg.vars_() == []:
            return Con(math.exp(simple_arg.ev({})))
        return Exp(simple_arg)


class Sin(UnEx):
    op = 'Sin'

    def fun(self, inner):
        return math.sin(inner)

    def diff(self, var):
        if type(self.arg).__name__ == "str":
            return Cos(self.arg)
        else:
            return Cos(self.arg) * self.arg.diff(var)

    def simplify(self):
        simple_arg = self.arg.simplify()

        if simple_arg.vars_() == []:
            return Con(math.sin(simple_arg.ev({})))
        return Sin(simple_arg)


class Cos(UnEx):
    op = 'Cos'

    def fun(self, inner):
        return math.cos(inner)

    def diff(self, var):
        if type(self.arg).__name__ == "str":
            return Sin(self.arg)
        else:
            return -Sin(self.arg) * self.arg.diff(var)

    def simplify(self):
        simple_arg = self.arg.simplify()

        if simple_arg.vars_() == []:
            return Con(math.cos(simple_arg.ev({})))
        return Cos(simple_arg)


class Log(UnEx):
    op = 'Log'
    def fun(self, inner):
        return math.log(inner)

    def diff(self, var):
        return 1 / self.arg.ev(var)

    def simplify(self):
        simple_arg = self.arg.simplify()

        if simple_arg.vars_() == []:
            return Con(math.log(simple_arg.ev({})))
        return Log(simple_arg)

def diff(string, var):
    res = ParseAExpr().parse(string)
    if res != []:
        expr = result(res)
        return str(expr.diff(var).simplify())
   

if __name__ == "__main__":
    # print(Exp(Con(5)) == Exp(Con(5)))
    # print(Exp(Var("x") * (Var("y") + Con(5))).diff("x"))
    # print(Exp(Var("x") * (Var("y") + Con(-5) + Con(5))).simplify().diff("x").simplify())
    # print(Plus(Con(0), Con(0)))
    # print(Exp(Plus(Con(3),Con(2))).simplify())
    # nu = Con(0)
    # ein = Con(1)
    # zwe = Con(2)
    # ix = Var('x')
    # ip = Var('y')
    # fu = ip * ix
    # f1 = fu.diff('x').simplify()
    # print((-ix * -Con(5)).diff('x').simplify())
    # print(Cos(-ix * Con(5)).diff('x'))
    # print(Times(ix, ix).diff('x').simplify())
    # print(-Sin(ix*-Con(8)+Con(5)*-Var('y')-Con(9)).ev({'x':7, 'y':13}))
    # print(And(Var('x'), Var('y')))
    # print(Equal(Var('x'), Var('y')))
    print(result(ParseExpon().parse("exp(5)")).ev({}))
    print(type(Con(5).toZ3()))
    print(Con(5).toZ3())


