
from program_types import *
from AST import *
from Tokens import *
from parse_util import *

# Dépendances circulaires...
import parseBlock

def parseType(tokenizer, omitFirtParenthesis, start=None):
    token = tokenizer.current()
    if start == None: start = token.pos()[0]
    end = None

    if omitFirtParenthesis or token.isSymbol(Symbol.LPAR):
        contents = []

        while True:
            if not omitFirtParenthesis:
                tokenizer.nextToken()
            omitFirtParenthesis = False

            c = parseType(tokenizer, False)
            contents.append(c)
            token = tokenizer.nextToken()

            if token.isSymbol(Symbol.COMMA):
                continue
            elif token.isSymbol(Symbol.RPAR):
                end = token.pos()[1]
                break
            else:
                raise ASTError(
                    token.pos(),
                    "Expected ',' or ')'."
                )

        # Nécessairement, len(contents) != 0.
        if len(contents) == 1:
            return contents[0]
        else:
            return TupleType((start, end), contents)
    elif token.isType(TokenType.IDENTIFIER):
        name = token.getValue()

        if tokenizer.lookahead().isSymbol(Symbol.LT):
            if name != "GenericBox":
                raise ASTError(
                    token.pos(),
                    "Expected 'GenericBox' for generic arguments."
                )

            tokenizer.nextToken()
            genericName = expectIdentifier(tokenizer.nextToken())
            expectSymbol(tokenizer.nextToken(), Symbol.GT)
            end = tokenizer.current().pos()[1]

            return GenericBoxType((start, end), genericName)
        elif tokenizer.lookahead().isSymbol(Symbol.LPAR):
            tokenizer.nextToken()
            wrapped = parseType(tokenizer, False)
            end = tokenizer.current().pos()[1]

            if name == "Box":
                return BoxType((start, end), wrapped)
            elif name == "List":
                return ListType((start, end), wrapped)
            else:
                raise ASTError(
                    token.pos(),
                    "Expected 'Box'."
                )
        else:
            if name == "Integer":
                return Integer
            elif name == "Boolean":
                return Boolean
            elif name == "String":
                return String
            else:
                raise ASTError(
                    token.pos(), "Unknown type '{}'.".format(name)
                )
    else:
        raise ASTError(token.pos(), "Expected '(' or an identifier.")

def parseFnArgs(tokenizer):
    # Renvoie un quadruplet (pos, argTypes, args, type)
    # où "args" est la liste des noms des arguments de la fonction.

    argTypes = []
    args = []
    peek = tokenizer.lookahead()
    start = peek.pos()[0]
    type = None

    if peek.isKeyword(Keyword.VOID):
        tokenizer.nextToken()

        expectSymbol(tokenizer.nextToken(), Symbol.RARROW)

        tokenizer.nextToken()
        if tokenizer.current().isKeyword(Keyword.VOID):
            type = Void
        else:
            type = parseType(tokenizer, False)

        end = tokenizer.current().pos()[1]
        pos = (start, end)

        return pos, [Void], [], type

    while True:
        if not tokenizer.lookahead().isSymbol(Symbol.LPAR):
            tokenizer.nextToken()
            if tokenizer.current().isKeyword(Keyword.VOID):
                type = Void
            else:
                type = parseType(tokenizer, False)
            break

        # On est certains que ce sera bien le symbole '('.
        lpar = tokenizer.nextToken()
        tokenizer.nextToken()

        if not tokenizer.lookahead().isSymbol(Symbol.COLON):
            type = parseType(tokenizer, True, lpar.pos()[0])
            break

        nameToken = tokenizer.current()
        name = expectIdentifier(nameToken)
        namePos = nameToken.pos()
        expectSymbol(tokenizer.nextToken(), Symbol.COLON)
        tokenizer.nextToken()
        type = parseType(tokenizer, False)

        rpar = tokenizer.nextToken()
        expectSymbol(rpar, Symbol.RPAR)

        peek = tokenizer.lookahead()

        if peek.isSymbol(Symbol.RARROW):
            argTypes.append(type)
            args.append(Var(namePos, name))
            token = tokenizer.nextToken()
            continue
        else:
            raise ASTError(peek.pos(), "Expected '->', ',' or ')'.")


    end = tokenizer.current().pos()[1]
    pos = (start, end)

    if len(args) == 0:
        raise ASTError(
            pos,
            "Expected at least one argument."
        )

    return pos, argTypes, args, type

def parseFunction(tokenizer):
    first = tokenizer.nextToken()
    start = first.pos()[0]
    expectKeyword(first, Keyword.FN)
    name = expectIdentifier(tokenizer.nextToken())
    expectSymbol(tokenizer.nextToken(), Symbol.COLON)
    typePos, argTypes, args, retType = parseFnArgs(tokenizer)
    type = FunctionType(typePos, argTypes, retType)

    body = parseBlock.parseBlock(tokenizer)
    end = body.pos()[1]

    return Function((start, end), name, type, args, body)
