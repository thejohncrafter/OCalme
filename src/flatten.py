
from collections import deque

from program_types import *
from flatIR import *

def assertTypeMatch(
    ltype, rtype, lpos, rpos,
    evaluateGenerics=False,
    genericMap=None
):
    encounteredBoxes = []

    if evaluateGenerics and genericMap == None:
        # On a besoin de "genericMap" dans ce cas,
        # mais c'est une erreur dans le compilateur
        # qui ne devrait donc jamais arriver :
        # pas besoin de donner de beau message d'erreur.
        raise NotImplemented()

    def internalMatcher(ltype, rtype, lpos, rpos):
        if ltype == None:
            return
        else:
            if isinstance(rtype, TupleType):
                rpos = rtype.pos()

                if not isinstance(ltype, TupleType):
                    raise FlattenError(
                        lpos, rpos,
                        "Expected {}, got {}.".format(
                            ltype.type_repr(),
                            rtype.type_repr()
                        )
                    )

                lpos = ltype.pos()

                if len(ltype.contents) != len(rtype.contents):
                    raise FlattenError(
                        lpos, rpos,
                        (
                            "Expected {}, got {}" +
                            "(mismatched tuple lengths)."
                        ).format(
                            ltype.type_repr(),
                            rtype.type_repr()
                        )
                    )

                for i, content_rtype in enumerate(rtype.contents):
                    content_ltype = ltype.contents[i]
                    internalMatcher(
                        content_ltype, content_rtype,
                        lpos, rpos
                    )
            elif isinstance(rtype, BoxType):
                lwrapped = None
                rwrapped = rtype.wrapped

                if evaluateGenerics and isinstance(ltype, GenericBoxType):
                    if ltype.genericName in genericMap:
                        lwrapped = genericMap[ltype.genericName]
                    else:
                        genericMap[ltype.genericName] = rwrapped
                        encounteredBoxes.append((ltype, rtype))
                        return
                elif not isinstance(ltype, BoxType):
                    raise FlattenError(
                        lpos, rpos,
                        "Expected {}, got {}.".format(
                            ltype.type_repr(),
                            rtype.type_repr()
                        )
                    )
                else:
                    lwrapped = ltype.wrapped
                    rwrapped = rtype.wrapped

                if (ltype, rtype) in encounteredBoxes:
                    return
                encounteredBoxes.append((ltype, rtype))

                internalMatcher(
                    lwrapped, rwrapped, lpos, rpos
                )
            elif isinstance(rtype, GenericBoxType):
                if not isinstance(ltype, GenericBoxType) or \
                    ltype.genericName != rtype.genericName:
                    raise FlattenError(
                        lpos, rpos,
                        "Expected {}, got {}.".format(
                            ltype.type_repr(),
                            rtype.type_repr()
                        )
                    )
            elif rtype == Void or isUnitType(rtype):
                if ltype == None:
                    return
                if ltype == rtype:
                    return

                raise FlattenError(
                    lpos, rpos,
                    "Expected {}, got {}.".format(
                        ltype.type_repr(), rtype.type_repr()
                    )
                )
            else:
                raise NotImplemented()

    internalMatcher(ltype, rtype, lpos, rpos)

def expandLValue(varstack, lvalue, rtype, rpos):
    assertTypeMatch(
        lvalue.type, rtype,
        lvalue.pos(), rpos
    )

    def createVars(pos, rtype):
        # Cette fonctions crée toutes les variables nécessaires
        # pour recevoir un tuple du type donné.

        created = []
        for c in rtype.contents:
            if isinstance(c, TupleType):
                created.extend(createVars(pos, c))
            elif isUnitType(c):
                var = varstack.createUnnamedVar(pos, lvalue.context)
                var.type = c
                created.append(var)
            else:
                raise NotImplemented()

        return created

    # On veut que "lvalue" soit du type "rtype", où
    # "lvalue" est de type "TypedTuple", mais
    # on ne sais pas si "lvalue" correspond exactement
    # au type "rtype": par exemple, on peut avoir :
    #   - lvalue = (x, y);
    #   - rtype = (1, (2, 3)).
    # Dans ce cas, il faudra créer des variables anonymes
    # pour pouvoir "aplatir" "(2, 3)" dans "y".

    def expandInternals(varstack, index, lvalue, rtype):
        if isinstance(rtype, TupleType):
            if not isinstance(lvalue, Tuple):
                created = createVars(lvalue.pos(), rtype)
                lvalue.type = rtype
                lvalue.markVirtual(VirtualVarType.TUPLE, created)
                return created, index + 1
            else:
                vars = []
                for content_rtype in rtype.contents:
                    lhs = lvalue.contents[index]
                    vars_below, index = \
                        expandInternals(
                            varstack, index, lhs, content_rtype
                        )
                    vars.extend(vars_below)
                return vars, index
        elif isinstance(rtype, BoxType):
            lvalue.type = rtype
            return [lvalue], index + 1
        elif isinstance(rtype, GenericBoxType):
            lvalue.type = rtype
            return [lvalue], index + 1
        elif isUnitType(rtype):
            lvalue.type = rtype
            return [lvalue], index + 1
        else:
            raise NotImplemented()

    if isinstance(rtype, TupleType):
        lvalue_contents, _ = expandInternals(
            varstack, 0, lvalue, rtype
        )
        lvalue = TypedTuple(lvalue.pos(), rtype, lvalue_contents)

    lvalue.type = rtype
    return lvalue

def flattenTupleContents(pos, contents):
    # Renvoie un doublet (type, flatContents)
    flatContents = []
    type = TupleType(pos, [c.type for c in contents])

    for c in contents:
        if isinstance(c.type, TupleType) :
            flatContents.extend(c.contents)
        elif c.type == None or isUnitType(c.type):
            flatContents.append(c)
        else:
            raise NotImplemented()

    return type, flatContents

def flattenArith(varstack, arith):
    assignments = []
    operands = [None for _ in arith.operands]
    op = arith.op
    operandType = None

    if op == Operation.CONCAT:
        operandType = String
    elif op == Operation.AND or op == Operation.OR:
        operandType = Boolean
    elif op == Operation.ADD or op == Operation.MUL or \
        op == Operation.SUB or op == Operation.DIV:
        operandType = Integer
    else:
        raise NotImplemented()

    for i, o in enumerate(arith.operands):
        a, rvalue = flattenRValue(varstack, o)
        assignments.extend(a)
        assertTypeMatch(
            operandType, rvalue.type, arith.pos(), rvalue.pos()
        )
        operands[i] = rvalue

    return assignments, TypedArith(
        arith.pos(), operandType, arith.op, operands
    )

def flattenCmp(varstack, cmp):
    input = deque(cmp.cmps)
    assignments = []

    def expectOperand():
        if len(input) == 0:
            raise ASTError(
                cmp.pos(),
                "Too short, expected an operand."
            )

        type, r = input.popleft()

        if type != Comparison.OPERAND:
            raise ASTError(
                r,
                "Expected an operand."
            )

        operands = []

        for val in r:
            a, val = flattenRValue(varstack, val)
            assignments.extend(a)

            assertTypeMatch(
                Integer, val.type, cmp.pos(), val.pos()
            )

            if not isinstance(val, TypedVar):
                var = varstack.createUnnamedVar(val.pos())
                var.type = Integer
                assignments.append(
                    Assign(val.pos(), var, val)
                )
                val = var

            operands.append(val)

        return operands

    def expectOperator():
        if len(input) == 0:
            raise ASTError(
                cmp.pos(),
                "Too short, expected an operator."
            )

        type, r = input.popleft()

        if type == Comparison.OPERAND:
            raise ASTError(
                cmp.pos(),
                "Maflormed (expected an operator). " +
                "This error may be due to the parser."
            )

        return r, type

    splitCmps = []

    lop = None
    op_pos = None
    op = None
    rop = None

    lop = expectOperand()

    while True:
        op_pos, op = expectOperator()
        rop = expectOperand()

        for l in lop:
            for r in rop:
                splitCmps.append(TypedCmp(op_pos, l, op, r))

        if len(input) != 0:
            lop = rop
        else:
            break

    vars = []

    for c in splitCmps:
        var = varstack.createUnnamedVar(c.pos())
        var.type = Boolean
        vars.append(var)
        assignments.append(
            Assign(
                c.pos(),
                var,
                c
            )
        )

    return assignments, TypedArith(
        cmp.pos(),
        Boolean,
        Operation.AND,
        vars
    )

def instantiateGenerics(rtype, genericMap):
    visited = {}
    # La gestion des types génériques pourrait être _beaucoup_
    # plus propre, à voir si jamais j'implémente des types
    # définis pas l'utilisateur.
    # (En attendant, ça marche, dont on ne touche pas...)

    def visitRType(rtype):
        nonlocal visited

        if isinstance(rtype, TupleType):
            contents = [
                visitRType(el) for el in rtype.contents
            ]
            return TupleType(rtype.pos(), contents)
        elif isinstance(rtype, ListType):
            if rtype in visited:
                return visited[rtype]
            else:
                typed = ListType(
                    rtype.pos(),
                    visitRType(rtype.contentType)
                )
                visited[rtype] = typed
                return typed
        elif isinstance(rtype, BoxType):
            if rtype in visited:
                return visited[rtype]
            else:
                typed = BoxType(
                    rtype.pos(),
                    None
                )
                visited[rtype] = typed
                typed.contentType = visitRType(rtype.wrapped)
                return typed
        elif isinstance(rtype, GenericBoxType):
            return BoxType(rtype.pos(), genericMap[rtype.genericName])
        elif isUnitType(rtype):
            return rtype
        else:
            raise NotImplemented()
    return visitRType(rtype)

def flattenCall(varstack, call):
    if not isinstance(call.target, Var):
        raise NotImplemented()

    target = call.target.name

    ftype = varstack.findFunctionType(target, call.target.pos())
    assignments = []
    args = []
    out = []
    output = []
    lvalue = None

    if len(ftype.args) == 1 and ftype.args[0] == Void:
        if not len(call.args) == 0:
            raise ASTError(
                call.pos(),
                "Expected no argument for a void type function."
            )
    elif len(ftype.args) != len(call.args):
        raise ASTError(
            call.pos(),
            "Argument count does not match the function's signature."
        )

    genericMap = {}

    for i, arg in enumerate(call.args):
        a, val = flattenRValue(varstack, call.args[i])
        assignments.extend(a)

        assertTypeMatch(
            ftype.args[i],
            val.type,
            call.pos(),
            call.args[i].pos(),
            True,
            genericMap
        )

        if isinstance(val.type, TupleType):
            args.extend(val.contents)
        else:
            args.append(val)

    if ftype.ret != Void:
        lvalue = varstack.createUnnamedVar(call.pos())
        retType = instantiateGenerics(ftype.ret, genericMap)
        lvalue = expandLValue(varstack, lvalue, retType, call.pos())

        if isinstance(lvalue.type, TupleType):
            out = lvalue.contents
        else:
            out = [lvalue]

    if isinstance(ftype, NativeFunction):
        assignments.append(NativeCall(call.pos(), target, args, out))
    else:
        assignments.append(FlatCall(call.pos(), target, args, out))

    if ftype.ret != Void:
        return assignments, lvalue
    else:
        return assignments, VoidValue(call.pos())

def buildIfValue(varstack, pos, aIfTrue, aElse, valIfTrue, valElse):
    # Retourne un triplet (value, aIfTrue, aElse)
    # où "value" est la variable qui contiendra l'éventuelle
    # valeur du "if".

    if valIfTrue.type != Void and valElse == None:
        raise FlattenError(
            valIfTrue.pos(),
            pos,
            "Expected an \"else\" clause, as this block returns a value."
        )

    value = VoidValue(pos)

    if valIfTrue.type != Void:
        value = varstack.createUnnamedVar(pos)
        value.type = valIfTrue.type
        aIfTrue.extend(
            assign(varstack, valIfTrue.pos(), value, valIfTrue)
        )
        aElse.extend(
            assign(varstack, valElse.pos(), value, valElse)
        )

    return value, aIfTrue, aElse

def flattenIf(varstack, ifBlock):
    assignments, cond = flattenRValue(varstack, ifBlock.cond)
    assertTypeMatch(
        Boolean, cond.type, ifBlock.pos(), cond.pos()
    )

    aIfTrue, valIfTrue = flattenRValue(varstack, ifBlock.valIfTrue)
    aElse = []
    valElse = None

    if ifBlock.valElse != None:
        aElse, valElse = flattenRValue(varstack, ifBlock.valElse)
        assertTypeMatch(
            valIfTrue.type, valElse.type, valIfTrue.pos(), valElse.pos()
        )

    value, aIfTrue, aElse = buildIfValue(
        varstack, ifBlock.pos(),
        aIfTrue, aElse,
        valIfTrue, valElse
    )

    assignments.append(
        TypedIf(ifBlock.pos(), cond, aIfTrue, aElse)
    )

    return assignments, value

def flattenIfUnwrap(varstack, ifBlock):
    assignments, box = flattenRValue(varstack, ifBlock.box)

    if not isinstance(box.type, BoxType):
        raise ASTError(
            box.pos(),
            "Expected a 'Box'."
        )

    fullFlag = varstack.createUnnamedVar(box.pos())
    fullFlag.type = Boolean
    assignments.append(
        NativeCall(ifBlock.box.pos(), "full", [box], [fullFlag])
    )

    # Si la "Box" est pleine, alors on la déballe sur "target".
    varstack.pushContext()
    varstack.enableLetMode()
    target = flattenLValue(varstack, ifBlock.target)
    varstack.disableLetMode()

    target = expandLValue(
        varstack, target, box.type.wrapped, target.pos()
    )
    out = None

    if isinstance(target.type, TupleType):
        out = target.contents
    else:
        out = [target]

    aIfTrue = [
        NativeCall(ifBlock.box.pos(), "unwrap", [box], out)
    ]

    a, valIfTrue = flattenRValue(varstack, ifBlock.valIfTrue)
    aIfTrue.extend(a)
    varstack.popContext()

    aElse = []
    valElse = None

    if ifBlock.valElse != None:
        aElse, valElse = flattenRValue(varstack, ifBlock.valElse)
        assertTypeMatch(
            valIfTrue.type, valElse.type, valIfTrue.pos(), valElse.pos()
        )

    value, aIfTrue, aElse = buildIfValue(
        varstack, ifBlock.pos(),
        aIfTrue, aElse,
        valIfTrue, valElse
    )

    assignments.append(
        TypedIf(ifBlock.pos(), fullFlag, aIfTrue, aElse)
    )

    return assignments, value

def flattenLoop(varstack, loopBlock):
    loopvar = varstack.createUnnamedLoop(loopBlock.pos())
    assignments, val = flattenBlock(varstack, loopBlock.block)
    # "val" ne contiendra que des opérations sans effets
    # de bord, on peut donc simplement l'ignorer.

    if loopvar.type == None or loopvar.type == Void:
        return [
            TypedLoop(loopBlock.pos(), loopvar.loopid, assignments)
        ], VoidValue(loopBlock.pos())
    else:
        return [
            TypedLoop(loopBlock.pos(), loopvar.loopid, assignments)
        ], loopvar

def flattenWrap(varstack, pos, target):
    assignments, rvalue = flattenRValue(varstack, target)

    if rvalue.type == Void:
        raise ASTError(
            target.pos(),
            "Can't wrap 'void'."
        )

    box = varstack.createUnnamedVar(pos)
    box.type = BoxType(pos, rvalue.type)
    input = None

    if isinstance(rvalue, TypedTuple):
        input = rvalue.contents
    else:
        input = [rvalue]

    assignments.append(
        NativeCall(pos, "wrap", input, [box])
    )

    return assignments, box

def flattenWrapEmpty(varstack, pos, type):
    if type == Void:
        raise ASTError(
            target.pos(),
            "Can't wrap 'void'."
        )

    box = varstack.createUnnamedVar(pos)
    box.type = BoxType(pos, type)

    return [NativeCall(pos, "wrap_empty", [], [box])], box

def flattenCons(varstack, pos, element, list):
    assignments, element = flattenRValue(varstack, element)
    a, list = flattenRValue(varstack, list)
    assignments.extend(a)

    if not isinstance(list.type, ListType):
        raise ASTError(
            list.pos(),
            "Expected a 'List'."
        )

    assertTypeMatch(
        element.type, list.type.contentType, element.pos(), list.pos()
    )

    if element.type == Void:
        raise ASTError(
            pos,
            "Can't cons 'Void'."
        )

    input = []

    if isinstance(element, TypedTuple):
        input = element.contents
    else:
        input = [element]

    input.append(list)

    box = varstack.createUnnamedVar(pos)
    box.type = ListType(pos, element.type)
    assignments.append(
        NativeCall(pos, "wrap", input, [box])
    )

    return assignments, box

def flattenConsEmpty(varstack, pos, type):
    if type == Void:
        raise ASTError(
            pos,
            "Can't cons 'Void'."
        )

    box = varstack.createUnnamedVar(pos)
    box.type = ListType(pos, type)

    return [NativeCall(pos, "wrap_empty", [], [box])], box

def flattenBreak(varstack, breakBlock):
    voidValue = VoidValue(breakBlock.pos())
    assignments, rvalue = [], voidValue

    if breakBlock.value != None:
        assignments, rvalue = flattenRValue(varstack, breakBlock.value)

    loopvar = varstack.findTopLoop(breakBlock.pos())

    if loopvar.type == None:
        loopvar.type = rvalue.type
        # Utile pour les messages d'erreurs.
        loopvar.setPos(rvalue.pos())
    else:
        assertTypeMatch(
            loopvar.type, loopvar.pos(), rvalue.type, rvalue.pos()
        )

    if rvalue.type != Void:
        assignments.extend(
            assign(varstack, breakBlock.pos(), loopvar, rvalue)
        )

    assignments.append(TypedBreak(breakBlock.pos(), loopvar.loopid))
    return assignments, voidValue

def flattenLValue(varstack, value):
    if isinstance(value, Var):
        return varstack.findOrCreateVar(value.name, value.pos())
    elif isinstance(value, Tuple):
        typedContents = [
            flattenLValue(varstack, el) for el in value.contents
        ]
        type, flatContents = flattenTupleContents(
            value.pos(), typedContents
        )
        return TypedTuple(value.pos(), type, flatContents)
    else:
        raise NotImplemented()

def flattenRValue(varstack, value):
    if isinstance(value, Block):
        return flattenBlock(varstack, value)
    elif isinstance(value, Tuple):
        typedContents = [None for _ in value.contents]
        assignments = []

        for i, c in enumerate(value.contents):
            a, v = flattenRValue(varstack, c)
            assignments.extend(a)
            typedContents[i] = v

        type, flatContents = flattenTupleContents(
            value.pos(),
            typedContents
        )
        return assignments, TypedTuple(value.pos(), type, flatContents)
    elif isinstance(value, Var):
        var = varstack.findVar(value.name, value.pos())

        if var.virtualType == VirtualVarType.TUPLE:
            return [], TypedTuple(
                var.pos(), var.type,
                var.virtualContents
            )
        elif var.virtualType == VirtualVarType.REAL:
            return [], var
        else:
            raise NotImplemented()
    elif isinstance(value, Constant):
        return [], TypedConstant(value.pos(), value.type, value.val)
    elif isinstance(value, Arith):
        return flattenArith(varstack, value)
    elif isinstance(value, Cmp):
        return flattenCmp(varstack, value)
    elif isinstance(value, Unary):
        op = value.op

        def buildOp(type):
            a, v = flattenRValue(varstack, value.target)
            type = None
            return a, TypedUnary(value.pos(), type, op, v)

        if op == Operation.NOT:
            return buildOp(Boolean)
        else:
            raise NotImplemented()
    elif isinstance(value, Call):
        return flattenCall(varstack, value)
    elif isinstance(value, IfBlock):
        return flattenIf(varstack, value)
    elif isinstance(value, IfUnwrapBlock):
        return flattenIfUnwrap(varstack, value)
    elif isinstance(value, LoopBlock):
        return flattenLoop(varstack, value)
    elif isinstance(value, Break):
        return flattenBreak(varstack, value)
    elif isinstance(value, Wrap):
        return flattenWrap(varstack, value.pos(), value.target)
    elif isinstance(value, WrapEmpty):
        return flattenWrapEmpty(varstack, value.pos(), value.type)
    elif isinstance(value, Cons):
        return flattenCons(
            varstack, value.pos(), value.element, value.list
        )
    elif isinstance(value, ConsEmpty):
        return flattenConsEmpty(varstack, value.pos(), value.type)
    else:
        raise NotImplemented()

def assign(varstack, pos, lvalue, rvalue):
    lvalue = expandLValue(varstack, lvalue, rvalue.type, rvalue.pos())

    def uncheckedAssign(lvalue, rvalue):
        if isinstance(lvalue, Tuple):
            assignments = []

            for i, rhs in enumerate(rvalue.contents):
                lhs = lvalue.contents[i]
                assignments.extend(uncheckedAssign(lhs, rhs))

            return assignments
        elif isinstance(lvalue, TypedVar):
            # Dans ce cas, "rvalue" n'est pas un Tuple.
            # (Car "lvalue" a été modifiée par expandLValue
            # pour correspondre au type de "rvalue".)
            if rvalue.type == Void:
                raise FlattenError(
                    lvalue.pos(),
                    rvalue.pos(),
                    "Can't assign a value of type \"void\"."
                )

            return [Assign(pos, lvalue, rvalue)]
        else:
            raise NotImplemented()

    # "expandLValue" a déjà vérifié que les types sont compatibles.
    return uncheckedAssign(lvalue, rvalue)

def flattenBlock(varstack, block):
    varstack.pushContext()
    assignments = []
    blockValue = VoidValue(block.pos())

    for cmd in block.commands:
        if isinstance(cmd, Let):
            lvalue = cmd.lvalue
            rvalue = cmd.rvalue

            a, rvalue = flattenRValue(varstack, rvalue)
            varstack.enableLetMode()
            lvalue = flattenLValue(varstack, lvalue)
            varstack.disableLetMode()

            assignments.extend(a)
            assignments.extend(
                assign(varstack, cmd.pos(), lvalue, rvalue)
            )
        elif isinstance(cmd, Set):
            lvalue = cmd.lvalue
            rvalue = cmd.rvalue

            a, rvalue = flattenRValue(varstack, rvalue)
            lvalue = flattenLValue(varstack, lvalue)

            assignments.extend(a)
            assignments.extend(
                assign(varstack, cmd.pos(), lvalue, rvalue)
            )
        elif isinstance(cmd, BlockReturn):
            a, blockValue = flattenRValue(varstack, cmd.value)
            assignments.extend(a)
        else:
            a, val = flattenRValue(varstack, cmd)
            # "val" ne contiendra que des opérations sans effets
            # de bord, on peut donc simplement l'ignorer.
            assignments.extend(a)

    varstack.popContext()

    if blockValue.type == Void:
        return assignments, blockValue
    else:
        out = varstack.createUnnamedVar(block.pos())
        assignments.extend(
            assign(varstack, block.pos(), out, blockValue)
        )

        if out.virtualType == VirtualVarType.TUPLE:
            return assignments, TypedTuple(
                out.pos(), out.type,
                out.virtualContents
            )
        else:
            return assignments, out

def flattenFunction(varstack, type, value):
    varstack.pushContext()
    varstack.enableLetMode()
    args = []

    for i, arg in enumerate(value.args):
        argtype = type.args[i]
        var = varstack.findOrCreateVar(arg.name, arg.pos())
        var.type = argtype
        args.append(var)

    varstack.disableLetMode()

    assignments, blockValue = flattenBlock(varstack, value.body)
    functionValue = None

    if isinstance(blockValue, TypedTuple):
        functionValue = blockValue.contents
    elif isinstance(blockValue, VoidValue):
        functionValue = []
    else:
        functionValue = [blockValue]

    assertTypeMatch(
        type.ret, blockValue.type,
        type.pos(), blockValue.pos()
    )

    varstack.popContext()

    return TypedFunction(
        value.pos(),
        blockValue.type,
        value.name,
        varstack.dumpVars(),
        args,
        assignments,
        functionValue
    )
