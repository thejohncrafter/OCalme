
from enum import Enum, auto

from AST import *
from program_types import *

class FlattenError(BaseException):
    def __init__(self, lpos, rpos, reason):
        self.args = [
            "{} and {} : \n{}".format(
                formatPos(lpos),
                formatPos(rpos),
                reason
            )
        ]

class VoidValue(CodeEntity):
    def __init__(self, pos):
        super().__init__(pos)
        self.type = Void

    def pretty(self, n):
        return "(void)"

class Assign(CodeEntity):
    def __init__(self, pos, l, r):
        super().__init__(pos)
        self.l = l
        self.r = r

    def pretty(self, n):
        return "{} <- {}".format(self.l.pretty(n), self.r.pretty(n))

class VirtualVarType(Enum):
    REAL = auto()
    TUPLE = auto()

class TypedVar(CodeEntity):
    def __init__(self, pos, type, context):
        super().__init__(pos)
        self.type = type
        self.id = -1
        self.context = context
        # Ce champ vaut autre chause que "REAL" pour une variable dite
        # "virtuelle", c'est à dire uniquement utilisée par le
        # "flattener/typechecker" pour gérer les variables contenant
        # des Tuples.
        self.virtualType = VirtualVarType.REAL
        self.virtualContents = None

    def setId(self, id):
        self.id = id

    def markVirtual(self, virtualType, contents):
        self.virtualType = virtualType
        self.virtualContents = contents

    def type_repr(self):
        if self.type == None:
            return "_"
        else:
            return self.type.type_repr()

    def pretty(self, n):
        if self.virtualType == VirtualVarType.TUPLE:
            contents = ""

            for c in self.virtualContents:
                contents += "\n{}{},".format(tabs(n+2), c.pretty(n+2))

            return (
                "(\n{}virt. {}," +
                "\n{}contents=[{}\n{}]\n{})"
            ).format(
                tabs(n+1),
                self.type_repr(),
                tabs(n+1),
                contents,
                tabs(n+1),
                tabs(n)
            )
        else:
            repr = "None"
            if self.type != None:
                repr = self.type.type_repr()

            return "({}: {})".format(self.id, repr)

class LoopVar(TypedVar):
    def __init__(self, pos, type, context, loopid):
        super().__init__(pos, type, context)
        self.loopid = loopid

    def setPos(self, pos):
        self._pos = pos

class TypedConstant(Constant):
    def type_repr(self):
        return self.type.type_repr()

    def pretty(self, n):
        return "({})".format(self.type_repr())

class TypedTuple(Tuple):
    # Dans cette représentation des "Tuples", la structure
    # est définie par "self.type", mais le contenu ("self.contents")
    # est "plat": c'est seulement une liste de "TypedVar"
    # (et de "TypedConstant").

    def __init__(self, pos, type, contents):
        super().__init__(pos, contents)
        self.type = type

    def type_repr(self):
        return self.type.type_repr()

    def pretty(self, n):
        contents = ""

        for c in self.contents:
            contents += "\n{}{},".format(tabs(n+2), c.pretty(n+2))

        return (
            "TypedTuple(\n{}type={}," +
            "\n{}contents=[{}\n{}]\n{})"
        ).format(
            tabs(n+1),
            self.type_repr(),
            tabs(n+1),
            contents,
            tabs(n+1),
            tabs(n)
        )

class TypedArith(Arith):
    def __init__(self, pos, type, op, operands):
        super().__init__(pos, op, operands)
        self.type = type

class TypedUnary(Unary):
    def __init__(self, pos, type, op, target):
        super().__init__(pos, op, target)

class TypedCmp(CodeEntity):
    def __init__(self, pos, lop, op, rop):
        super().__init__(pos)
        self.lop = lop
        self.op = op
        self.rop = rop

    def pretty(self, n):
        return "TypedCmp(\n{}lop={}\n{}op={}\n{}rop={}\n{})".format(
            tabs(n+1),
            self.lop.pretty(n+1),
            tabs(n+1),
            self.op.pretty(n+1),
            tabs(n+1),
            self.rop.pretty(n+1),
            tabs(n)
        )

def prettyCommands(commands):
    out = ""

    for c in commands:
        out += "\n{}{},".format(tabs(n+2), c.pretty(n+2))

    return out

class FlatCallBase(CodeEntity):
    def __init__(self, pos, target, input, output):
        super().__init__(pos)
        self.target = target
        self.input = input
        self.output = output

    def pretty(self, n):
        input = ""
        output = ""

        for v in self.input:
            input += "\n{}{},".format(tabs(n+2), v.pretty(n+2))
        for v in self.output:
            output += "\n{}{},".format(tabs(n+2), v.pretty(n+2))

        return (
            "{}(\n{}target={}\n{}input=[{}\n{}]," +
            "\n{}output=[{}\n{}]\n{})"
        ).format(
            self.className,
            tabs(n+1),
            self.target,
            tabs(n+1),
            input,
            tabs(n+1),
            tabs(n+1),
            output,
            tabs(n+1),
            tabs(n)
        )

class FlatCall(FlatCallBase):
    className = "FlatCall"

class NativeCall(FlatCallBase):
    className = "NativeCall"

class TypedIf(CodeEntity):
    def __init__(self, pos, cond, aIfTrue, aElse):
        # "aElse" _peut_ valoir None.
        super().__init__(pos)
        self.cond = cond
        self.aIfTrue = aIfTrue
        self.aElse = aElse

    def pretty(self, n):
        aIfTrue = ""
        aElse = ""

        for c in self.aIfTrue:
            aIfTrue += "\n{}{},".format(tabs(n+2), c.pretty(n+2))

        for c in self.aElse:
            aElse += "\n{}{},".format(tabs(n+2), c.pretty(n+2))

        return (
            "TypedIf(\n{}cond={}," +
            "\n{}aIfTrue=[{}\n{}],\n{}aElse=[{}\n{}]\n{})"
        ).format(
            tabs(n+1),
            self.cond.pretty(n+1),
            tabs(n+1),
            aIfTrue,
            tabs(n+1),
            tabs(n+1),
            aElse,
            tabs(n+1),
            tabs(n)
        )

class TypedLoop(CodeEntity):
    def __init__(self, pos, loopid, commands):
        super().__init__(pos)
        self.loopid = loopid
        self.commands = commands

    def pretty(self, n):
        commands = ""

        for c in self.commands:
            commands += "\n{}{},".format(tabs(n+2), c.pretty(n+2))

        return (
            "TypedLoop(\n{}loopid={}\n{}commands=[{}\n{}]\n{})"
        ).format(
            tabs(n+1),
            self.loopid,
            tabs(n+1),
            commands,
            tabs(n+1),
            tabs(n)
        )

class TypedBreak(CodeEntity):
    def __init__(self, pos, loopid):
        super().__init__(pos)
        self.loopid = loopid

    def pretty(self, n):
        return "TypedBreak(loopid={})".format(self.loopid)

class TypedFunction(CodeEntity):
    def __init__(self, pos, type, name, vars, args, commands, value):
        super().__init__(pos)
        self.type = type
        self.name = name
        self.vars = vars
        self.args = args
        self.commands = commands
        self.value = value

    def pretty(self, n):
        vars = ""
        args = ""
        commands = ""
        value = ""

        for v in self.vars:
            vars += "\n{}{},".format(tabs(n+2), v.pretty(n+1))

        for a in self.args:
            args += "\n{}{},".format(tabs(n+2), a.pretty(n+1))

        for c in self.commands:
            commands += "\n{}{},".format(tabs(n+2), c.pretty(n+2))

        for v in self.value:
            value += "\n{}{}".format(tabs(n+2), v.pretty(n+2))

        return (
            "TypedFunction(\n{}name=\"{}\"\n{}vars=[{}\n{}]," +
            "\n{}args=[{}\n{}],\n{}commands=[{}\n{}]," +
            "\n{}value=[{}\n{}]\n{})"
        ).format(
            tabs(n+1),
            self.name,
            tabs(n+1),
            vars,
            tabs(n+1),
            tabs(n+1),
            args,
            tabs(n+1),
            tabs(n+1),
            commands,
            tabs(n+1),
            tabs(n+1),
            value,
            tabs(n+1),
            tabs(n)
        )
