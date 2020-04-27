
from enum import Enum, auto
from AST import *
from Tokens import *

class PrecedenceBuilder:
    class Flags(Enum):
        OPERAND = auto()
        CONCAT = auto()
        OR = auto()
        AND = auto()
        ADD = auto()
        SUB = auto()
        MUL = auto()
        DIV = auto()

    def __init__(self):
        self.top = (None, [])
        self.root = self.top
        self.prec_stack = [(-1, self.root)]
        self.topPrec = -1
        self.lastOperand = None

    def precedence(self, op):
        if op == Operation.CONCAT:
            return 0
        elif op == Operation.OR:
            return 1
        elif op == Operation.AND:
            return 2
        elif op == Operation.ADD:
            return 3
        elif op == Operation.SUB:
            return 4
        elif op == Operation.MUL:
            return 5
        elif op == Operation.DIV:
            return 6
        else:
            raise ASTError(None, "Unknown operation.")

    def matchingFlag(self, op):
        if op == Operation.CONCAT:
            return PrecedenceBuilder.Flags.CONCAT
        elif op == Operation.OR:
            return PrecedenceBuilder.Flags.OR
        elif op == Operation.AND:
            return PrecedenceBuilder.Flags.AND
        elif op == Operation.ADD:
            return PrecedenceBuilder.Flags.ADD
        elif op == Operation.SUB:
            return PrecedenceBuilder.Flags.SUB
        elif op == Operation.MUL:
            return PrecedenceBuilder.Flags.MUL
        elif op == Operation.DIV:
            return PrecedenceBuilder.Flags.DIV
        else:
            raise ASTError(None, "Unknown operation.")

    def matchingOperation(self, op):
        if op == PrecedenceBuilder.Flags.CONCAT:
            return Operation.CONCAT
        elif op == PrecedenceBuilder.Flags.OR:
            return Operation.OR
        elif op == PrecedenceBuilder.Flags.AND:
            return Operation.AND
        elif op == PrecedenceBuilder.Flags.ADD:
            return Operation.ADD
        elif op == PrecedenceBuilder.Flags.SUB:
            return Operation.SUB
        elif op == PrecedenceBuilder.Flags.MUL:
            return Operation.MUL
        elif op == PrecedenceBuilder.Flags.DIV:
            return Operation.DIV

    def descendPrec(self, prec):
        formerTop = self.top

        while True:
            if len(self.prec_stack) == 0:
                self.top = (None, [self.root])
                self.topPrec = -1
                self.root = self.top
                self.prec_stack = [(-1, self.root)]
                break

            (stack_max, node) = self.prec_stack[-1]
            if stack_max <= prec:
                self.top = node
                self.topPrec = stack_max
                break

            self.prec_stack.pop()

            if self.lastOperand != None:
                self.top[1].append(self.lastOperand)
                self.lastOperand = None

    def receiveOperator(self, operator):
        prec = self.precedence(operator)
        self.descendPrec(prec)

        if self.top[0] == None:
            top = (self.matchingFlag(operator), self.top[1])
            self.root = top
            self.top = top
            self.prec_stack = [(prec, top)]
            self.topPrec = prec
        elif prec > self.topPrec:
            self.topPrec = prec
            top = (self.matchingFlag(operator), [])
            self.top[1].append(top)
            self.top = top
            self.prec_stack.append((prec, top))

        if self.lastOperand != None:
            self.top[1].append(self.lastOperand)
            self.lastOperand = None

    def receiveOperand(self, operand):
        if self.lastOperand != None:
            self.top[1].append(self.lastOperand)
            self.lastOperand = None

        self.lastOperand = (PrecedenceBuilder.Flags.OPERAND, operand)

    def finalize(self, start, end):
        if self.lastOperand != None:
            self.top[1].append(self.lastOperand)
            self.lastOperand = None

        def buildArith(pair):
            if pair[0] == PrecedenceBuilder.Flags.OPERAND:
                return pair[1]
            op = self.matchingOperation(pair[0])
            operands = [buildArith(el) for el in pair[1]]
            return Arith((start, end), op, operands)

        if self.root[0] == None:
            if len(self.root[1]) > 1:
                raise ASTError(None, "Missing an operator.")
            if len(self.root[1]) == 0:
                return None
            return buildArith(self.root[1][0])

        return buildArith(self.root)
