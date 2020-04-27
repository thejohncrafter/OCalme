
from enum import Enum, auto

from flatIR import *

class Varstack():
    class Flag(Enum):
        ANON = auto()
        VAR = auto()
        LOOP = auto()

        # Ce type de boucle sera utile
        # pour implémenter l'évaluation paresseuse.
        GEN_LOOP = auto()

    def __init__(self, functions):
        self.functions = functions
        self.varstack = []
        self.reserved = []
        self.letMode = False
        self.all = []
        self.nextLoopId = 0

    def findFunctionType(self, name, pos):
        # "pos" est utilisé pour le sourcemapping des exceptions.

        for fname, type in self.functions[::-1]:
            if fname == name:
                return type

        print(name)
        print(self.functions)

        raise ASTError(pos, "Can't find function {}.".format(name))
        # TODO: Should produce a propper error.
        raise NotImplemented()

    def findOrCreateVar(self, name, pos):
        if self.letMode:
            # On peut créer des variables,
            # mais pas assigner des variables réservées.
            for varname, var in self.reserved:
                if varname == name:
                    raise FlattenError(
                        var.pos(), pos,
                        "Can't define a variable twice in a let."
                    )

            var = TypedVar(pos, None, self.varstack[-1])
            self.varstack[-1].append(((Varstack.Flag.VAR, name), var))
            self.reserved.append((name, var))
            return var
        else:
            # On cherche la variable si elle a déjà été définie,
            # et on lève une exception si elle ne l'a jamais été.
            for vars in self.varstack[::-1]:
                for (flag, varname), var in vars[::-1]:
                    if flag != Varstack.Flag.VAR:
                        continue
                    if varname == name:
                        return var

            raise ASTError(
                pos,
                "This variable has never been defined."
            )
        return var

    def findLoop(self, name, pos):
        # Même principe que "findOrCreateVar" lorsque "letMode = False".
        for vars in self.varstack[::-1]:
            for (flag, varname), var in vars[::-1]:
                if flag != Varstack.Flag.LOOP:
                    continue
                if varname == name:
                    return var

        raise ASTError(
            pos,
            "Loop '{}' has never been defined.".format(name)
        )

    def findTopLoop(self, pos):
        # On cherche simplement une boucle.
        # (Une boucle définie par l'utilisateur, pas une boucle
        # générée par le compilateur.)
        for vars in self.varstack[::-1]:
            for (flag, varname), var in vars[::-1]:
                if flag == Varstack.Flag.LOOP:
                    return var

        raise ASTError(
            pos,
            "There is no enclosing loop.".format(name)
        )

    def createUnnamedVar(self, pos, context=None):
        if context == None:
            context = self.varstack[-1]

        var = TypedVar(pos, None, self.varstack[-1])
        context.append(((Varstack.Flag.ANON, None), var))
        return var

    def _generateLoopId(self):
        id = self.nextLoopId
        self.nextLoopId += 1
        return id

    def createLoop(self, pos, name):
        # Renvoie un couple (id, var).
        var = LoopVar(
            pos, None, self.varstack[-1], self._generateLoopId()
        )
        self.varstack[-1].append(((Varstack.Flag.LOOP, name), var))
        return var

    def createUnnamedLoop(self, pos):
        # Renvoie un couple (id, var).
        var = LoopVar(
            pos, None, self.varstack[-1], self._generateLoopId()
        )
        self.varstack[-1].append(((Varstack.Flag.LOOP, None), var))
        return var

    def createGeneratedLoop(self, pos):
        # Renvoie un couple (id, var).
        var = LoopVar(
            pos, None, self.varstack[-1], self._generateLoopId()
        )
        self.varstack[-1].append(((Varstack.Flag.GEN_LOOP, None), var))
        return var

    def findVar(self, name, pos):
        # Recherche la variable dans "self.varstack".
        # Lève une exception si la variable n'est pas définie.

        for vars in self.varstack[::-1]:
            for (flag, varname), var in vars[::-1]:
                if flag != Varstack.Flag.VAR:
                    continue
                if varname == name:
                    return var

        raise ASTError(
            pos,
            "This variable has never been defined."
        )

    def enableLetMode(self):
        # Permet de créer des variables
        # pour une lvalue dans un "let".
        self.reserved = []
        self.letMode = True

    def disableLetMode(self):
        # Revient au mode normal, i.e. ce Varstack fonctionne
        # maintenant comme en dehors d'une lvalue de "let".
        self.letMode = False

    def pushContext(self):
        self.varstack.append([])

    def popContext(self):
        top = self.varstack.pop()
        vars = []
        i = len(self.all)

        for _, var in top:
            if var.virtualType != VirtualVarType.REAL:
                continue
            var.setId(i)
            vars.append(var)
            i += 1

        self.all.extend(vars)

    def dumpVars(self):
        # Renvoie toutes les variables crées
        # et vide "self.all".
        all = self.all
        self.all = []
        return all
