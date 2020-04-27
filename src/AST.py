
from enum import Enum, auto

from program_types import *

def formatPos(pos):
    ((l1, c1), (l2, c2)) = pos
    if l1 == l2:
        return "At l.{}, col.{}:{}".format(l1, c1, c2)
    else:
        return "From l.{}, col.{} to l.{}, col.{}".format(
                l1, c1, l2, c2
            )

class ASTError(BaseException):
    def __init__(self, pos, reason):
        if pos == None:
            self.args = ["(unknown position): \n{}".format(reason)]
            return
        self.args = ["{} :\n{}".format(formatPos(pos), reason)]

def tabs(n):
    return "    " * n

class Block(CodeEntity):
    def __init__(self, pos, commands):
        super().__init__(pos)
        self.commands = commands

    def pretty(self, n):
        commands = ""

        for c in self.commands:
            commands += "\n{}{},".format(tabs(n+1), c.pretty(n+1))

        return "Block([{}\n{}])".format(
            commands,
            tabs(n)
        )

class Let(CodeEntity):
    def __init__(self, pos, lvalue, rvalue):
        super().__init__(pos)
        self.lvalue = lvalue
        self.rvalue = rvalue

    def pretty(self, n):
        return "Let(\n{}lvalue={},\n{}rvalue={}\n{})".format(
            tabs(n+1),
            self.lvalue.pretty(n+1),
            tabs(n+1),
            self.rvalue.pretty(n+1),
            tabs(n)
        )

class Set(CodeEntity):
    def __init__(self, pos, lvalue, rvalue):
        super().__init__(pos)
        self.lvalue = lvalue
        self.rvalue = rvalue

    def pretty(self, n):
        return "Set(\n{}lvalue={},\n{}rvalue={}\n{})".format(
            tabs(n+1),
            self.lvalue.pretty(n+1),
            tabs(n+1),
            self.rvalue.pretty(n+1),
            tabs(n)
        )

class Return(CodeEntity):
    def __init__(self, pos, value):
        super().__init__(pos)
        self.value = value

    def pretty(self, n):
        return "Return(\n{}value={}\n{})".format(
            tabs(n+1),
            self.value.pretty(n+1),
            tabs(n)
        )

class BlockReturn(CodeEntity):
    def __init__(self, pos, value):
        super().__init__(pos)
        self.value = value

    def pretty(self, n):
        return "BlockReturn(\n{}value={}\n{})".format(
            tabs(n+1),
            self.value.pretty(n+1),
            tabs(n)
        )

class Break(CodeEntity):
    def __init__(self, pos, value):
        super().__init__(pos)
        self.value = value

    def pretty(self, n):
        value = "(none)"

        if self.value != None:
            value = self.value.pretty(n+1)

        return "Break(\n{}value={}\n{})".format(
            tabs(n+1),
            value,
            tabs(n)
        )

class Call(CodeEntity):
    def __init__(self, pos, target, args):
        super().__init__(pos)
        self.target = target
        self.args = args

    def pretty(self, n):
        args = ""

        for a in self.args:
            args += "\n{}{},".format(tabs(n+2), a.pretty(n+2))

        return "Call(\n{}target={},\n{}args=[{}\n{}]\n{})".format(
            tabs(n+1),
            self.target.pretty(n+1),
            tabs(n+1),
            args,
            tabs(n+1),
            tabs(n)
        )

class Var(CodeEntity):
    def __init__(self, pos, name):
        super().__init__(pos)
        self.name = name

    def pretty(self, n):
        return "Var(name=\"{}\")".format(self.name)

class Arith(CodeEntity):
    def __init__(self, pos, op, operands):
        super().__init__(pos)
        self.op = op
        self.operands = operands

    def pretty(self, n):
        operands = ""

        for o in self.operands:
            operands += "\n{}{},".format(tabs(n+2), o.pretty(n+2))

        return "Arith(\n{}op={},\n{}operands=[{}\n{}]\n{})".format(
            tabs(n+1),
            self.op.pretty(n+1),
            tabs(n+1),
            operands,
            tabs(n+1),
            tabs(n)
        )

class Cmp(CodeEntity):
    def __init__(self, pos, cmps):
        super().__init__(pos)
        self.cmps = cmps

    def pretty(self, n):
        cmps = ""

        def formatOperand(oplist):
            l = ""

            for o in oplist:
                l += '\n{}{}'.format(tabs(n+2), o.pretty(n+2))

            return "[{}\n{}]".format(l, tabs(n+1))

        for op, r in self.cmps:
            content = None

            if op == Comparison.OPERAND:
                content = formatOperand(r)
            else:
                content = op.pretty(n+1)

            cmps += "\n{}{}".format(tabs(n+1), content)

        return "Cmp({}\n{})".format(cmps, tabs(n))

class Unary(CodeEntity):
    def __init__(self, pos, op, target):
        super().__init__(pos)
        self.op = op
        self.target = target

    def pretty(self, n):
        return "Unary(\n{}op={},\n{}target={}\n{})".format(
            tabs(n+1),
            self.op.pretty(n+1),
            tabs(n+1),
            self.target.pretty(n+1),
            tabs(n)
        )

class Constant(CodeEntity):
    def __init__(self, pos, type, val):
        super().__init__(pos)
        self.type = type
        self.val = val

    def pretty(self, n):
        return "Constant(type={}, val={})".format(
            self.type.pretty(n+1),
            self.val.__repr__()
        )

class Tuple(CodeEntity):
    def __init__(self, pos, contents):
        super().__init__(pos)
        self.contents = contents

    def pretty(self, n):
        contents = ""

        for c in self.contents:
            contents += "\n{}{},".format(tabs(n+1), c.pretty(n+1))

        return "Tuple({}\n{})".format(
            contents,
            tabs(n),
        )

class IfBlock(CodeEntity):
    def __init__(self, pos, cond, valIfTrue, valElse):
        # "valElse" vaut éventuellemnt "None"
        super().__init__(pos)
        self.cond = cond
        self.valIfTrue = valIfTrue
        self.valElse = valElse

    def pretty(self, n):
        valElse = "(void)"

        if self.valElse != None:
            valElse = self.valElse.pretty(n+1)

        return (
            "IfBlock(\n{}cond={},\n{}valIfTrue={}," +
             "\n{}valElse={}\n{})"
        ).format(
            tabs(n+1),
            self.cond.pretty(n+1),
            tabs(n+1),
            self.valIfTrue.pretty(n+1),
            tabs(n+1),
            valElse,
            tabs(n)
        )

class IfUnwrapBlock(CodeEntity):
    def __init__(self, pos, box, target, valIfTrue, valElse):
        # "valElse" vaut éventuellemnt "None"
        super().__init__(pos)
        self.box = box
        self.target = target
        self.valIfTrue = valIfTrue
        self.valElse = valElse

    def pretty(self, n):
        valElse = "(void)"

        if self.valElse != None:
            valElse = self.valElse.pretty(n+1)

        return (
            "IfUnwrapBlock(\n{}box={},\n{}target={},\n{}valIfTrue={}," +
             "\n{}valElse={}\n{})"
        ).format(
            tabs(n+1),
            self.box.pretty(n+1),
            tabs(n+1),
            self.target.pretty(n+1),
            tabs(n+1),
            self.valIfTrue.pretty(n+1),
            tabs(n+1),
            valElse,
            tabs(n)
        )

class LoopBlock(CodeEntity):
    def __init__(self, pos, block):
        super().__init__(pos)
        self.block = block

    def pretty(self, n):
        return "LoopBlock({})".format(self.block.pretty(n))

class Wrap(CodeEntity):
    def __init__(self, pos, target):
        super().__init__(pos)
        self.target = target

    def pretty(self, n):
        return "Wrap(\n{}target={}\n{})".format(
            tabs(n+1),
            self.target.pretty(n+1),
            tabs(n)
        )

class WrapEmpty(CodeEntity):
    def __init__(self, pos, type):
        super().__init__(pos)
        self.type = type

    def pretty(self, n):
        return "WrapEmpty(\n{}type={}\n{})".format(
            tabs(n+1),
            self.type.pretty(n+1),
            tabs(n)
        )

class Cons(CodeEntity):
    def __init__(self, pos, element, list):
        super().__init__(pos)
        self.element = element
        self.list = list

    def pretty(self, n):
        return "Cons(\n{}element={},\n{}list={}\n{})".format(
            tabs(n+1),
            self.element.pretty(n+1),
            tabs(n+1),
            list,
            tabs(n)
        )

class ConsEmpty(CodeEntity):
    def __init__(self, pos, type):
        super().__init__(pos)
        self.type = type

    def pretty(self, n):
        return "ConsEmpty(\n{}type={}\n{})".format(
            tabs(n+1),
            self.type.pretty(n+1),
            tabs(n)
        )

class Function(CodeEntity):
    def __init__(self, pos, name, type, args, body):
        super().__init__(pos)
        self.name = name
        self.args = args
        self.type = type
        self.body = body

    def pretty(self, n):
        args = ""
        retType = "None"

        for a in self.args:
            args += "\n{}{},".format(tabs(n+2), a.pretty(n+2))

        return ("Function(\n{}name=\"{}\"\n{}type=\"{}\"," +
            "\n{}args=[{}\n{}],\n{}body={}\n{})"
        ).format(
            tabs(n+1),
            self.name,
            tabs(n+1),
            self.type.type_repr(),
            tabs(n+1),
            args,
            tabs(n+1),
            tabs(n+1),
            self.body.pretty(n+1),
            tabs(n)
        )
