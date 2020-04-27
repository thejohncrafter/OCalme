
from AST import ASTError
from Tokens import *

def expectSymbol(token, symbol):
    if not token.isSymbol(symbol):
        raise ASTError(
            token.pos(),
            "Expected '{}'.".format(symbol.value)
        )

def expectKeyword(token, keyword):
    if not token.isKeyword(keyword):
        raise ASTError(
            token.pos(),
            "Expected '{}'.".format(keyword.value)
        )

def expectIdentifier(token):
    if not token.isType(TokenType.IDENTIFIER):
        raise ASTError(token.pos(), "Expected an identifier.")

    return token.getValue()
