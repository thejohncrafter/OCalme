from enum import Enum, auto

class TokenType(Enum):
    # Token "virtuel", utilisé par le parseur
    # Représente un fragement de texte qui a déjà été parsé.
    PARSED = auto()
    EOF = auto()
    SYMBOL = auto()
    KEYWORD = auto()
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()

class Symbol(Enum):
    LPAR = '('
    RPAR = ')'
    LBRACKET = '{'
    RBRACKET = '}'

    CONCAT = '@'
    OR = '||'
    AND = '&&'
    NOT = '!'
    ADD = '+'
    SUB = '-'
    MUL = '*'
    DIV = '/'

    LT = '<'
    LEQ = '<='
    GT = '>'
    GEQ = '>='
    EQ = '='

    SEMICOLON = ';'
    COLON = ':'
    COMMA = ','
    RARROW = '->'

class Keyword(Enum):
    RETURN = 'return'
    FN = 'fn'

    TRUE = 'true'
    FALSE = 'false'

    VOID = 'void'
    CONS = 'cons'
    WRAP = 'wrap'
    UNWRAP = 'unwrap'
    EMPTY = 'empty'

    IF = 'if'
    ON = 'on'
    THEN = 'then'
    ELSE = 'else'

    LOOP = 'loop'
    BREAK = 'break'

    LET = 'let'

class Token:
    def __init__(self, pair, start, end):
        self.pair = pair
        self.start = start
        self.end = end

    def isEOF(self):
        return self.pair[0] == TokenType.EOF

    def isType(self, type):
        return self.pair[0] == type

    def isLike(self, tokentype, token):
        return self.pair == (tokentype, token)

    def isSymbol(self, symbol):
        return self.isLike(TokenType.SYMBOL, symbol)

    def isKeyword(self, keyword):
        return self.isLike(TokenType.KEYWORD, keyword)

    def getValue(self):
        return self.pair[1]

    def pos(self):
        return (self.start, self.end)

    def __repr__(self):
        def getTokenRepresentation():
            tokentype = self.pair[0]
            if tokentype == TokenType.PARSED:
                return "{...}"
            elif tokentype == TokenType.EOF:
                return "_"
            elif tokentype == TokenType.SYMBOL:
                return self.pair[1].name
            elif tokentype == TokenType.KEYWORD:
                return self.pair[1].name
            elif tokentype == TokenType.IDENTIFIER:
                return "'{}'".format(self.pair[1])
            elif tokentype == TokenType.NUMBER:
                return "{}".format(self.pair[1])
            elif tokentype == TokenType.STRING:
                return "{}".format(repr(self.pair[1]))
            else:
                raise Exception(
                    "Unknown token type : {}.".format(tokentype)
                )
        tokentype = self.pair[0].name
        token = getTokenRepresentation()

        return "({}, {})".format(tokentype, token)
