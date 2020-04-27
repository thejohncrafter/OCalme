
from program_types import *
from flatIR import *

def transpileVar(var):
    id = var.id

    return "v{}".format(id)

def transpileUnary(unary):
    op = None

    if unary.op == Operation.NOT:
        op = "not "
    else:
        raise NotImplemented()

    operand = transpileOperand(unary.target)
    return "{}({})".format(op, operand)

def transpileArith(arith):
    op = None
    out = ""

    op_map = {
        Operation.CONCAT: '+',
        Operation.OR: ' or ',
        Operation.AND: ' and ',
        Operation.ADD: '+',
        Operation.SUB: '-',
        Operation.MUL: '*',
        Operation.DIV: '//'
    }

    if not arith.op in op_map:
        raise NotImplemented()

    op = op_map[arith.op]

    for i, operand in enumerate(arith.operands):
        if i != 0:
            out += op

        out += transpileOperand(operand)

    return "({})".format(out)

def transpileCmp(cmp):
    cmp_map = {
        Comparison.LT: '<',
        Comparison.LEQ: '<=',
        Comparison.GT: '>',
        Comparison.GEQ: '>=',
        Comparison.EQ: '=='
    }

    if not cmp.op in cmp_map:
        raise NotImplemented()
    op = cmp_map[cmp.op]

    return "({}{}{})".format(
        transpileOperand(cmp.lop),
        op,
        transpileOperand(cmp.rop)
    )

def transpileConstant(constant):
    if constant.type == Integer:
        return "{}".format(constant.val)
    elif constant.type == Boolean:
        return "{}".format(constant.val)
    elif constant.type == String:
        return repr(constant.val)
    else:
        raise NotImplemented()

def transpileOperand(operand):
    if isinstance(operand, Arith):
        return transpileArith(operand)
    elif isinstance(operand, Unary):
        return transpileUnary(operand)
    elif isinstance(operand, TypedVar):
        return transpileVar(operand)
    elif isinstance(operand, TypedCmp):
        return transpileCmp(operand)
    elif isinstance(operand, TypedConstant):
        return transpileConstant(operand)
    else:
        raise NotImplemented()

def transpileVarList(list):
    first = True
    out = ""

    for el in list:
        if not first:
            out += ","
        else:
            first = False

        out += transpileOperand(el)

    return out

def transpileCommands(indent, isInLoop, commands):
    out = ""
    tabs = "\t"*indent

    for comm in commands:
        if isinstance(comm, Assign):
            l = transpileVar(comm.l)
            r = transpileOperand(comm.r)
            out += "{}{}={}\n".format(tabs, l, r)
        elif isinstance(comm, FlatCall):
            l = transpileVarList(comm.output)
            r = transpileVarList(comm.input)
            f = "f_{}".format(comm.target)

            if len(comm.output) != 0:
                out += "{}{} = {}({})\n".format(tabs, l, f, r)
            else:
                out += "{}{}({})\n".format(tabs, f, r)
        elif isinstance(comm, NativeCall):
            l = transpileVarList(comm.output)
            r = transpileVarList(comm.input)
            f = comm.target
            cmd = ""

            if f == "full":
                cmd = "{}=({}[0]!=0)".format(l, r)
            elif f == "wrap":
                cmd = "{}=(mkBoxId(),({}))".format(l, r)
            elif f == "unwrap":
                cmd = "{}={}[1]".format(l, r)
            elif f == "wrap_empty":
                cmd = "{}=(0,None)".format(l)
            elif f == "print":
                cmd = "print({})".format(r)
            else:
                raise NotImplemented()

            out += "{}{}\n".format(tabs, cmd)
        elif isinstance(comm, TypedIf):
            cond = transpileOperand(comm.cond)
            hasIfClause = (len(comm.aIfTrue) != 0)
            cIfTrue = transpileCommands(
                indent + 1, isInLoop, comm.aIfTrue
            )
            hasElseClause = (len(comm.aElse) != 0)
            cElse = transpileCommands(
                indent + 1, isInLoop, comm.aElse
            )

            if hasIfClause:
                if hasElseClause:
                    out += "{}if {}:\n{}{}else:\n{}".format(
                        tabs,
                        cond,
                        cIfTrue,
                        tabs,
                        cElse
                    )
                else:
                    out += "{}if {}:\n{}".format(
                        tabs,
                        cond,
                        cIfTrue
                    )
        elif isinstance(comm, TypedLoop):
            body = transpileCommands(indent + 1, True, comm.commands)
            if body == "":
                body = "{}\tpass\n".format(tabs)

            tailFrag = ""
            if isInLoop:
                tailFrag = "{}if loopid!={}:\n{}\tbreak\n".format(
                    tabs,
                    comm.loopid,
                    tabs
                )
            out += "{}while True:\n{}{}".format(
                tabs,
                body,
                tailFrag
            )
        elif isinstance(comm, TypedBreak):
            out += "{}loopid={}\n{}break\n".format(
                tabs,
                comm.loopid,
                tabs
            )
        else:
            out += "{}{}\n".format(tabs, transpileOperand(comm))

    return out

def transpileFunction(function):
    name = function.name
    args = transpileVarList(function.args)
    body = transpileCommands(2, False, function.commands)
    value = transpileVarList(function.value)

    loopfrag = "\t\tloopid=0"

    if body != "":
        return "\tdef f_{}({}):\n{}\n{}\t\treturn {}\n".format(
            name, args, loopfrag, body, value
        )
    else:
        return "\tdef f_{}({}):\n{}\n\t\treturn {}\n".format(
            name, args, loopfrag, value
        )
