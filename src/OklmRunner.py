
from AST import *
from Tokens import *
from Tokenizer import Tokenizer, TokenizerError
from parse_util import *

from parseLRValue import parseLRValue
from parseBlock import parseBlock
from parseFunction import parseFunction

from Varstack import Varstack
from flatIR import *
from flatten import *
from transpile import *

def run(code, printAST, printIR, printGenerated, shouldExecute):
    nullPos = ((0, 0), (0, 0))
    natives = [
        (
            "print",
            NativeFunction(nullPos, [String], Void)
        )
    ]

    tokenizer = Tokenizer(code)
    # On réserve déjà les noms des fonction natives.
    fnames = [name for name, _ in natives]
    astFunctions = []
    functionTypes = [pair for pair in natives]
    irFunctions = []
    generated = (
        "\n" +
        "def wrapper():\n" +
            "\tnextId = 1\n" +
            "\tdef mkBoxId():\n" +
                "\t\tnonlocal nextId\n" +
                "\t\tid = nextId\n" +
                "\t\tnextId += 1\n" +
                "\t\treturn id\n" +
            "\n"
    )

    while True:
        if tokenizer.lookahead().isEOF():
            break

        ast = parseFunction(tokenizer)

        if ast.name in fnames:
            raise ASTError(
                ast.pos(),
                "Function '{}' already declared.".format(ast.name)
            )

        fnames.append(ast.name)
        astFunctions.append(ast)
        functionTypes.append((ast.name, ast.type))

    if printAST:
        for ast in astFunctions:
                print(ast.pretty(0))

    foundMain = False

    for name, type in functionTypes:
        if name == "main":
            foundMain = True
            typematch = True

            if not len(type.args) == 1:
                typematch = False
            elif not type.args[0] == Void:
                typematch = False
            elif not type.ret == Void:
                typematch = False

            if not typematch:
                raise ASTError(
                    type.pos(),
                    (
                        "Expected function 'main' to be typed " +
                        "'void -> void'"
                    )
                )

    if not foundMain:
        raise ASTError(
            nullPos,
            "Can't find function 'main'."
        )

    varstack = Varstack(functionTypes)
    for name, type in functionTypes:
        #print("{}: {}".format(name, type.type_repr()))
        pass

    for ast in astFunctions:
        flat = flattenFunction(varstack, ast.type, ast)
        irFunctions.append(flat)

    if printIR:
        for ir in irFunctions:
            print(ir.pretty(0))

    for flat in irFunctions:
        generated += transpileFunction(flat)

    generated += "\n\tf_main()\nwrapper()\n"

    if printGenerated:
        print(generated)

    #print("\nGenerated :")
    #print(generated)
    #print()
    if shouldExecute:
        exec(generated)
