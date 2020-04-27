
from enum import Enum, auto

class NotImplemented(BaseException):
    def __init__(self):
        self.args = ["Not implemented."]

class CodeEntity:
    def __init__(self, pos):
        self._pos = pos

    def pos(self):
        return self._pos

class Operation(Enum):
    NOT = auto()

    CONCAT = auto()
    AND = auto()
    OR = auto()
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()

    def pretty(self, n):
        return self.name

class Comparison(Enum):
    OPERAND = auto()

    LT = auto()
    LEQ = auto()
    GT = auto()
    GEQ = auto()
    EQ = auto()

    def pretty(self, n):
        return self.name

class Type():
    def type_repr():
        raise NotImplemented()

def _buildUnitType(name):
    class _UnitType(Type):
        def __init__(self):
            pass

        def pretty(self, n):
            return name

        def type_repr(self):
            return name

    return _UnitType()

Void = _buildUnitType("void")
Integer = _buildUnitType("Integer")
Boolean = _buildUnitType("Boolean")
String = _buildUnitType("String")

def isUnitType(type):
    return type == Integer or type == Boolean or type == String

class BoxType(Type):
    def __init__(self, pos, wrapped):
        self._pos = pos
        self.wrapped = wrapped

    def pos(self):
        return self._pos

    def type_repr(self):
        return "Box({})".format(self.wrapped.type_repr())

    def pretty(self, n):
        return self.type_repr()

class GenericBoxType(Type):
    def __init__(self, pos, genericName):
        self._pos = pos
        self.genericName = genericName

    def pos(self):
        return self._pos

    def type_repr(self):
        return "GenericBox<{}>".format(self.genericName)

    def pretty(self, n):
        return self.type_repr()

class ListType(BoxType):
    def __init__(self, pos, contentType):
        super().__init__(pos, TupleType(pos, [contentType, self]))
        self.contentType = contentType

    def type_repr(self):
        return "List({})".format(self.contentType.type_repr())

class TupleType(Type):
    def __init__(self, pos, contents):
        self._pos = pos
        self.contents = contents

    def pos(self):
        return self._pos

    def type_repr(self):
        contents = ""

        for i, c in enumerate(self.contents):
            repr = "any"

            if c != None:
                repr = c.type_repr()

            if i == 0:
                contents += "{}".format(repr)
            else:
                contents += ", {}".format(repr)

        return "({})".format(contents)

class FunctionType(Type):
    def __init__(self, pos, args, ret):
        self._pos = pos
        self.args = args
        self.ret = ret

    def pos(self):
        return self._pos

    def type_repr(self):
        args = ""

        for arg in self.args:
            args += "{} -> ".format(arg.type_repr())

        return "{}{}".format(args, self.ret.type_repr())

class NativeFunction(FunctionType):
    def type_repr(self):
        return "(native) {}".format(super().type_repr())
