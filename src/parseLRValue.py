
from AST import *
from Tokens import *
from PrecedenceBuilder import PrecedenceBuilder
from parse_util import *

# Dépendances circulaires...
import parseFunction
import parseBlock

def parseArgs(tokenizer):
    # Renvoie un triplet (pos, isLValuable, args).

    args = []
    cmps = []
    isLValuable = True
    start = tokenizer.current().pos()[0]
    isTuple = True

    def finalize(finalPos):
        if isTuple:
            return (start, end), isLValuable, args
        else:
            if len(args) == 0:
                raise ASTError(
                    finalPos,
                    "Expected an argument."
                )

            cmps.append((Comparison.OPERAND, args))
            return (start, end), False, [Cmp((start, end), cmps)]

    def receiveComparator(pos, op):
        nonlocal args, isTuple

        isTuple = False

        if len(args) == 0:
            raise ASTError(
                pos,
                "Expected something to compare to."
            )

        cmps.append((Comparison.OPERAND, args))
        args = []
        cmps.append((op, pos))

    while True:
        argLValuable, arg = parseLRValue(tokenizer)
        isLValuable = isLValuable and argLValuable
        token = tokenizer.current()
        end = token.pos()[1]

        def expectArg(pos):
            if arg == None:
                raise ASTError(
                    pos,
                    "Expected an argument."
                )
            args.append(arg)

        cmp_dict = {
            Symbol.LT: Comparison.LT,
            Symbol.LEQ: Comparison.LEQ,
            Symbol.GT: Comparison.GT,
            Symbol.GEQ: Comparison.GEQ,
            Symbol.EQ: Comparison.EQ
        }

        if token.isSymbol(Symbol.COMMA):
            expectArg(token.pos())
        elif token.getValue() in cmp_dict:
            isLValuable = False
            expectArg(token.pos())
            receiveComparator(token.pos(), cmp_dict[token.getValue()])
        elif token.isSymbol(Symbol.RPAR):
            if arg != None:
                args.append(arg)
            return finalize(token.pos())
        else:
            raise ASTError(token.pos(), "Expected ',' or ')'.")

def parseMaybeArith(tokenizer):
    # Renvoie un couple (isLValuable, value).

    start = tokenizer.lookahead().pos()[0]
    builder = PrecedenceBuilder()
    isLValuable = True

    target = None
    expectOperand = True
    needOperand = False
    end = start

    unaryStack = []

    def finalize(start, end):
        built = builder.finalize(start, end)

        if isinstance(built, Arith):
            return False, built
        elif built == None:
            return False, None
        else:
            return isLValuable, built

    def parseOperand():
        nonlocal unaryStack, isLValuable, target, expectOperand, end

        token = None

        while True:
            token = tokenizer.nextToken()
            end = token.pos()[1]

            if token.isSymbol(Symbol.NOT):
                unaryStack.append((token.pos(), Operation.NOT))
            else:
                break

        def wrapUnary(target):
            nonlocal unaryStack

            for pos, unary in unaryStack[::-1]:
                target = Unary(pos, unary, target)

            unaryStack = []
            return target

        if token.isType(TokenType.IDENTIFIER):
            target = Var(token.pos(), token.getValue())
        elif token.isKeyword(Keyword.TRUE):
            target = Constant(token.pos(), Boolean, True)
            isLValuable = False
        elif token.isKeyword(Keyword.FALSE):
            target = Constant(token.pos(), Boolean, False)
            isLValuable = False
        elif token.isType(TokenType.NUMBER):
            target = Constant(token.pos(), Integer, token.getValue())
            isLValuable = False
        elif token.isType(TokenType.STRING):
            target = Constant(token.pos(), String, token.getValue())
            isLValuable = False
        elif token.isSymbol(Symbol.LPAR):
            pos, argsLValuable, contents = parseArgs(tokenizer)
            isLValuable = isLValuable and argsLValuable
            expectSymbol(tokenizer.current(), Symbol.RPAR)

            if len(contents) == 0:
                raise ASTError(
                    pos,
                    "Expected a value."
                )
            elif len(contents) == 1:
                target = contents[0]
            else:
                target = Tuple(pos, contents)
        else:
            if needOperand:
                raise ASTError(token.pos(), "Expected an operand.")
            return finalize(start, end)

        expectOperand = False

        token = tokenizer.nextToken()

        if token.isSymbol(Symbol.LPAR):
            pos, argsLValuable, args = parseArgs(tokenizer)
            isLValuable = isLValuable and argsLValuable
            expectSymbol(tokenizer.current(), Symbol.RPAR)
            tokenizer.nextToken()

            builder.receiveOperand(
                wrapUnary(Call(pos, target, args))
            )
        else:
            builder.receiveOperand(wrapUnary(target))

    def parseOperator():
        nonlocal target, expectOperand, needOperand, end

        token = tokenizer.current()

        if token.isSymbol(Symbol.CONCAT):
            builder.receiveOperator(Operation.CONCAT)
        elif token.isSymbol(Symbol.OR):
            builder.receiveOperator(Operation.OR)
        elif token.isSymbol(Symbol.AND):
            builder.receiveOperator(Operation.AND)
        elif token.isSymbol(Symbol.ADD):
            builder.receiveOperator(Operation.ADD)
        elif token.isSymbol(Symbol.MUL):
            builder.receiveOperator(Operation.MUL)
        elif token.isSymbol(Symbol.SUB):
            builder.receiveOperator(Operation.SUB)
        elif token.isSymbol(Symbol.DIV):
            builder.receiveOperator(Operation.DIV)
        else:
            return finalize(start, end)

        expectOperand = True
        needOperand = True

    while True:
        val = None

        if expectOperand:
            val = parseOperand()
        else:
            val = parseOperator()

        if val != None:
            return val

def parseIf(tokenizer):
    first = tokenizer.nextToken()
    start = first.pos()[0]
    expectKeyword(first, Keyword.IF)
    isUnwrapping = False

    if tokenizer.lookahead().isKeyword(Keyword.UNWRAP):
        tokenizer.nextToken()
        isUnwrapping = True

    token = tokenizer.current()
    # "cond" représente "box" dans le cas d'un "if unwrap".
    _, cond = parseLRValue(tokenizer)
    target = None

    if isUnwrapping:
        if cond == None:
            raise ASTError(
                token.pos(),
                "Expected a value to unwrap."
            )

        onToken = tokenizer.current()
        expectKeyword(onToken, Keyword.ON)
        isLValuable, target = parseLRValue(tokenizer)

        if target == None:
            raise ASTError(
                onToken.pos(),
                "Expected a value after 'on'."
            )
        elif not isLValuable:
            raise ASTError(
                target.pos(),
                "Expected a LValue."
            )
    else:
        if cond == None:
            raise ASTError(
                token.pos(),
                "Expected a condition."
            )

    thenToken = tokenizer.current()
    expectKeyword(thenToken, Keyword.THEN)
    _, valIfTrue = parseLRValue(tokenizer)

    if valIfTrue == None:
        raise ASTError(
            thenToken.pos(),
            "Expected a value after 'then'."
        )

    end = valIfTrue.pos()[1]
    valElse = None
    maybeElse = tokenizer.current()

    if maybeElse.isKeyword(Keyword.ELSE):
        _, valElse = parseLRValue(tokenizer)

        if valElse == None:
            raise ASTError(
                maybeElse.pos(),
                "Expected a value after 'else'."
            )

        end = valIfTrue.pos()[1]

    if isUnwrapping:
        return IfUnwrapBlock(
            (start, end), cond, target, valIfTrue, valElse
        )
    else:
        return IfBlock((start, end), cond, valIfTrue, valElse)

def parseLoop(tokenizer):
    first = tokenizer.nextToken()
    start = first.pos()[0]
    expectKeyword(first, Keyword.LOOP)
    body = parseBlock.parseBlock(tokenizer)
    end = body.pos()[1]
    tokenizer.nextToken()

    return LoopBlock((start, end), body)

def parseEmptyType(tokenizer):
    expectKeyword(tokenizer.nextToken(), Keyword.EMPTY)
    expectSymbol(tokenizer.nextToken(), Symbol.COLON)
    tokenizer.nextToken()
    type = parseFunction.parseType(tokenizer, False)
    return type

def parseWrap(tokenizer):
    token = tokenizer.nextToken()
    expectKeyword(token, Keyword.WRAP)
    start = token.pos()[0]

    if tokenizer.lookahead().isKeyword(Keyword.EMPTY):
        type = parseEmptyType(tokenizer)
        end = tokenizer.current().pos()[1]
        tokenizer.nextToken()
        return WrapEmpty((start, end), type)
    else:
        _, target = parseLRValue(tokenizer)
        end = tokenizer.current().pos()[1]
        return Wrap((start, end), target)

def parseCons(tokenizer):
    token = tokenizer.nextToken()
    expectKeyword(token, Keyword.CONS)
    start = token.pos()[0]

    if tokenizer.lookahead().isKeyword(Keyword.EMPTY):
        type = parseEmptyType(tokenizer)
        end = tokenizer.current().pos()[1]
        tokenizer.nextToken()
        return ConsEmpty((start, end), type)
    else:
        _, element = parseLRValue(tokenizer)
        expectSymbol(tokenizer.current(), Symbol.COMMA)
        _, list = parseLRValue(tokenizer)
        end = tokenizer.current().pos()[1]
        return Cons((start, end), element, list)

def parseLRValue(tokenizer):
    # Renvoie un couple (isLValuable, value).

    peek = tokenizer.lookahead()

    if peek.isSymbol(Symbol.LBRACKET):
        value = parseBlock.parseBlock(tokenizer)
        tokenizer.nextToken()
        return False, value
    elif peek.isKeyword(Keyword.IF):
        return False, parseIf(tokenizer)
    elif peek.isKeyword(Keyword.LOOP):
        return False, parseLoop(tokenizer)
    elif peek.isKeyword(Keyword.WRAP):
        return False, parseWrap(tokenizer)
    elif peek.isKeyword(Keyword.CONS):
        return False, parseCons(tokenizer)
    else:
        return parseMaybeArith(tokenizer)
