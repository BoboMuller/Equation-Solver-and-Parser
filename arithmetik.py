import math

class Expr:
    def __add__(self, other):
        return Plus(self, other)

    def __mul__(self, other):
        return Times(self, other)

    def diff(self, var):
        print("Error! diff not implemented")

    def simplify(self):
        return self

    def eval(self, env):
        print("Error! eval not implemented")

    def vars(self):
        print("Error! vars not implemented")

class Con(Expr):
    def __init__(self, val : float):
        self.val = val

    def __str__(self):
        return str(self.val) # f”{self.x}”

    def __eq__(self, other):
        if type(other) == Con:
            return self.val == other.val
        return False

    def diff(self, var):
        return Con(0)

    def eval(self, env):
        return self.val

    def vars(self):
        return []

class Var(Expr):
    def __init__(self, name : str):
        self.name = name

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if type(other) == Var:
            return self.name == other.name
        return False

    def diff(self, var):
        if self.name == var:
            return Con(1)
        return Con(0)

    def eval(self, env):
        return env[self.name]   # Schlüssel wert paar, wenn name gefunden, dann wird wert ausgegeben
                                # Var("x").eval({'x':3}) => 3

    def vars(self):
        return [self.name]

class UnOp(Expr):
    def __init__(self, arg : Expr):
        self.arg = arg

    def __str__(self):
        return f"{self.op}({self.arg})"

    def eval(self, env):
        argval = self.arg.eval(env)
        return math.exp(argval)

    def vars(self):
        return list(set(self.arg.vars()))

class BinOp(Expr):
    def __init__(self, left : Expr, right : Expr):
        self.left = left
        self.right = right

    def __str__(self):
        return f"({self.left} {self.op} {self.right})"

    def __eq__(self, other):
        if not isinstance(other, BinOp):
            return False
        return self.left == other.left and self.right == other.right and other.op == self.op

    def eval(self, env):
        left_val = self.left.eval(env)
        right_val = self.right.eval(env)
        return self.fun(left_val, right_val)

    def vars(self):
        return list(set(self.left.vars() + self.right.vars()))

class Plus(BinOp):
    op = '+'

    def fun(self, x, y):
        return x + y

    def diff(self, var):
        return self.left.diff(var) + self.right.diff(var)

    def simplify(self):
        ev_l = None
        ev_r = None
        simple_left = self.left.simplify()
        if simple_left.vars() == []:
            ev_l = simple_left.eval({})
        simple_right = self.right.simplify()

        if simple_right.vars() == []:
            ev_r = simple_right.eval({})

        if ev_l != None and ev_r != None:
            return Con(ev_l + ev_r)

        if ev_l == 0:
            return simple_right

        elif ev_r == 0:
            return simple_left

        else:
            return simple_left + simple_right

    def eval(self, env):
        left_val = self.left.eval(env)
        right_val = self.right.eval(env)
        return left_val + right_val

class Times(BinOp):
    op = '*'

    def fun(self, x, y):
        return x * y

    def diff(self, var):
        return self.left.diff(var) * self.right +\
                self.left * self.right.diff(var)

    def simplify(self):
        ev_l = None
        ev_r = None
        simple_left = self.left.simplify()

        if simple_left.vars() == []:
            ev_l = simple_left.eval({})
        simple_right = self.right.simplify()

        if simple_right.vars() == []:
            ev_r = simple_right.eval({})

        if ev_l != None and ev_r != None:
            return Con(ev_l * ev_r)

        if ev_l == 0 or ev_r == 0:
            return Con(0)

        elif ev_l == 1:
            return simple_right
        elif ev_r == 1:
            return simple_left
        else:
            return simple_left * simple_right



""""
Dₓ (f * g) = Dₓ f * g + f * Dₓ g
(f * g)’ = f’ * g + f * g’
"""

class Exp(UnOp):
    op = "exp"
    def simplify(self):
        simple_arg = self.arg.simplify()
        if simple_arg.vars() == []:
            return Con(math.exp(simple_arg.eval({})))
        return Exp(simple_arg)

    def diff(self, var):
        return self.arg * self.arg.diff(var)

env = {'x' : 2.3, 'y' : 1.5}


if __name__ == "__main__":
    # x = Var('x')
    # y = Con(5)
    # print(Times(x, Exp(Times(Con(3), Con(3)))).simplify())
    # print(Times(Con(5), Plus(Con(3), Con(4))).simplify())
    # print(Exp(Var("x") * (Var("y") + Con(5))).diff("x").simplify())
    # print(Var("x") + Con(5) == Var("x") + Con(5))
