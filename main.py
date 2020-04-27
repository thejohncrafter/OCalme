
import argparse
import sys
sys.path.insert(0, './src')

from AST import ASTError
from Tokenizer import TokenizerError
from flatIR import FlattenError
import OklmRunner

printStackTrace = False
try:
    parser = argparse.ArgumentParser(
        prog="OCalme",
        description="Compile & run a OCalme file."
    )
    parser.add_argument(
        "--ast", action="store_true", help="Show AST."
    )
    parser.add_argument(
        "--ir", action="store_true", help="Show IR."
    )
    parser.add_argument(
        "--gen", action="store_true", help="Show generated code."
    )
    parser.add_argument(
        "--norun", action="store_true", help="Don't run the file."
    )
    parser.add_argument(
        "--dev", action="store_true",
        help="Enable dev mode (prints error stack trace)."
    )
    parser.add_argument("file")
    args = parser.parse_args()
    printStackTrace = args.dev

    with open(args.file) as file:
        OklmRunner.run(
            file.read(),
            args.ast,
            args.ir,
            args.gen,
            (not args.norun)
        )
except (TokenizerError, ASTError, FlattenError) as err:
    print(err)
    if printStackTrace:
        print("\n\n")
        raise
