result = lambda p: p[0][0]
rest   = lambda p: p[0][1]

class Parser:
    def __xor__(self, other):
        return OrElse(self, other)

    def __rshift__(self, and_then):
        return Seq(self, and_then)
    
    def parse(self, inp):
        return self.parser.parse(inp)

class ParseItem(Parser):
    def parse(self, inp):
        if inp == "":
            return []
        return [(inp[0], inp[1:])]

class Return(Parser):
    def __init__(self, x):
        self.x = x

    def parse(self, inp):
        return [(self.x, inp)]

class Fail(Parser):
    def parse(self, inp):
        return []
    
class Seq(Parser):
    def __init__(self, first, and_then):
        self.first    = first
        self.and_then = and_then

    def parse(self, inp):
        p = self.first.parse(inp)
        if p == []:
            return []
        # p [(x_1, rest_1), (x_2, rest_2), ....]
        # rs = []
        # for x, rest in p:
        #  rs = rs + self.and_then(x).parse(rest)
        return self.and_then(result(p)).parse(rest(p))

class OrElse(Parser):
    def __init__(self, parser1, parser2):
        self.parser1 = parser1
        self.parser2 = parser2

    def parse(self, inp):
        p = self.parser1.parse(inp)
        if p != []:
            return p
        return self.parser2.parse(inp)
    
class ParseChar(Parser):
    def __init__(self, x):
        self.parser = ParseIf(lambda c: c == x)

class ParseIf(Parser):
    def __init__(self, pred):
        self.parser = ParseItem() >> (lambda c: Return(c) if pred(c) else Fail())
                      

class ParseSome(Parser):
    def __init__(self, parser):
        self.parser = parser                         >> (lambda x: \
                      (ParseSome(parser)^Return([])) >> (lambda xs: \
                       Return(cons(x, xs))))

class ParseMany(Parser):
    def __init__(self, parser):
        self.parser = ParseSome(parser) ^ Return([])

def cons(x, xs):
    """
    >>> cons("a", [])
    'a'
    >>> cons("a", "bc")
    'abc'
    >>> cons(2, [])
    [2]
    >>> cons(2, [1, 2, 3])
    [2, 1, 2, 3]
    """
    if xs == [] and type(x) == str:
        return x
    if type(xs) == str:
        return x + xs
    return [x] + xs


class ParseInt(Parser):
    """
    >>> ParseInt().parse("89abc")
    [(89, 'abc')]
    >>> ParseInt().parse("-89abc")
    [(-89, 'abc')]
    >>> ParseInt().parse("--89abc")
    []
    """
    def __init__(self):
        self.parser = (ParseChar('-') >> (lambda _: \
                       ParseNat()     >> (lambda n: \
                       Return(-n)))) ^ ParseNat()

class ParseNat(Parser):
    """
    >>> ParseNat().parse("89abc")
    [(89, 'abc')]
    >>> ParseNat().parse("-89abc")
    []
    """
    def __init__(self):
        self.parser = Seq(ParseSome(ParseDigit()), lambda ns: \
                          Return(int(ns)))
        
class ParseDigit(Parser):
    """
    >>> ParseDigit().parse("abc")
    []
    >>> ParseDigit().parse("8abc")
    [('8', 'abc')]
    >>> ParseDigit().parse("89abc")
    [('8', '9abc')]
    """
    def __init__(self):
        self.parser = ParseIf(lambda c: c in "0123456789")

class ParseIdent(Parser):
    """
    >>> ParseIdent().parse("x1")
    [('x1', '')]
    >>> ParseIdent().parse("1x")
    []
    """
    def __init__(self):
        self.parser = ParseIf(str.isalpha) >> (lambda c:
                      ParseMany(ParseIf(str.isalnum)) >> (lambda cs:
                      Return(cons(c, cs))))

class ParseToken(Parser):
    """
    >>> ParseToken(ParseChar('(')).parse("  (   abc")
    [('(', 'abc')]
    >>> ParseToken(ParseChar('(')).parse("  + ( abc")
    []
    """
    def __init__(self, parser):
        self.parser = ParseMany(ParseIf(str.isspace)) >> (lambda _:
                      parser                          >> (lambda res:
                      ParseMany(ParseIf(str.isspace)) >> (lambda _:
                      Return(res))))

class ParseString(Parser):
    """
    >>> ParseString("hello").parse("helloabc")
    [('hello', 'abc')]
    >>> ParseString("hello").parse("hello")
    [('hello', '')]
    >>> ParseString("hello").parse(" hello")
    []
    """
    def __init__(self, string):
        self.parser = Return('') if string == '' else \
                      ParseChar(string[0]) >> (lambda c: \
                      ParseString(string[1:]) >> (lambda cs: \
                      Return(cons(c, cs))))
        
class ParseSymbol(Parser):
    """
    >>> ParseSymbol("exp").parse("    exp   ")
    [('exp', '')]
    >>> ParseSymbol("exp").parse("   aexp  ")
    []
    """
    def __init__(self, string):
        self.parser = ParseToken(ParseString(string))

class ParseIdentifier(Parser):
    """
    >>> ParseIdentifier().parse("   x1   ")
    [('x1', '')]
    >>> ParseIdentifier().parse("1x")
    []
    """
    def __init__(self):
        self.parser = ParseToken(ParseIdent())
