
from AST import *
from Tokens import *
from parse_util import *

# Dépendances circulaires...
import parseLRValue

def parseCommand(tokenizer):
    # Renvoie un couple (isRValue, val).

    peek = tokenizer.lookahead()
    start = peek.pos()[0]

    if peek.isKeyword(Keyword.LET):
        tokenizer.nextToken()

        isLValuable, lvalue = parseLRValue.parseLRValue(tokenizer)

        if not isLValuable:
            raise ASTError(lvalue.pos(), "Expected a lvalue.")

        eq = tokenizer.current()
        expectSymbol(eq, Symbol.EQ)

        _, rvalue = parseLRValue.parseLRValue(tokenizer)

        if rvalue == None:
            raise ASTError(
                (
                    eq.pos()[1],
                    tokenizer.current().pos()[0]
                ),
                "Expected a value."
            )

        return False, Let(
            (peek.pos()[0], rvalue.pos()[1]), lvalue, rvalue
        )
    elif peek.isKeyword(Keyword.RETURN):
        raise NotImplemented()
        tokenizer.nextToken()
        _, val = parseLRValue.parseLRValue(tokenizer)
        return False, Return((start, val.pos()[1]), val)
    elif peek.isKeyword(Keyword.BREAK):
        token = tokenizer.nextToken()
        expectKeyword(token, Keyword.BREAK)
        _, val = parseLRValue.parseLRValue(tokenizer)
        start, end = token.pos()

        if val != None:
            end = val.pos()[1]

        return False, Break((start, end), val)
    else:
        isLValuable, val = parseLRValue.parseLRValue(tokenizer)

        if tokenizer.current().isSymbol(Symbol.EQ):
            if not isLValuable:
                raise ASTError(
                    val.pos(),
                    "Expected a LValue for assignment."
                )

            _, rvalue = parseLRValue.parseLRValue(tokenizer)

            if rvalue == None:
                raise ASTError(
                    (
                        eq.pos()[1],
                        tokenizer.current().pos()[0]
                    ),
                    "Expected a value."
                )

            return False, Set(
                (peek.pos()[0], rvalue.pos()[1]), val, rvalue
            )
        else:
            return True, val

def parseBlock(tokenizer):
    firstCommand = True
    command = None
    isRValue = False

    commands = []

    first = tokenizer.nextToken()
    start = first.pos()[0]
    expectSymbol(first, Symbol.LBRACKET)

    while True:
        if command != None:
            commands.append(command)

        if not firstCommand:
            expectSymbol(tokenizer.current(), Symbol.SEMICOLON)
        firstCommand = False

        isRValue, command = parseCommand(tokenizer)

        if tokenizer.current().isSymbol(Symbol.RBRACKET):
            break

    last = tokenizer.current()
    end = last.pos()[1]
    expectSymbol(last, Symbol.RBRACKET)

    if command == None:
        pass
    elif isRValue:
        commands.append(BlockReturn(command.pos(), command))
    else:
        commands.append(command)

    return Block((start, end), commands)
