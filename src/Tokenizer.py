from Tokens import *

class RecognizerFlag(Enum):
    WAITING = 0
    RECOGNIZED = 1
    REJECTED = 2

symbols = [(enum, enum.value) for enum in Symbol]
keywords = [(enum, enum.value) for enum in Keyword]

class TokenizerError(BaseException):
    def __init__(self, pos, reason):
        ((l, c1), (_, c2)) = pos
        self.args = ["At l.{}, col.{}:{} :\n{}".format(l, c1, c2, reason)]

class SymbolRecognizer:
    def __init__(self):
        self.i = 0
        self.candidates = [True for _ in range(len(symbols))]
        self.previouslyFound = None

    def reset(self):
        self.previouslyFound = None
        self.i = 0
        for i in range(len(self.candidates)):
            self.candidates[i] = True

    def consume(self, char):
        foundSymbol = False
        symbol = None
        moreSymbols = False
        stillCandidates = False

        for k, (candidate, seq) in enumerate(symbols):
            if not self.candidates[k]: continue

            if len(seq) == self.i:
                self.candidates[k] = False
            elif char != seq[self.i]:
                self.candidates[k] = False
            else:
                if stillCandidates:
                    moreSymbols = True

                stillCandidates = True

                if self.i + 1 != len(seq): continue

                foundSymbol = True
                self.previouslyFound = candidate
                symbol = candidate

        self.i += 1

        if not stillCandidates:
            if self.previouslyFound != None:
                previouslyFound = self.previouslyFound
                self.previouslyFound = None
                return (
                    RecognizerFlag.REJECTED,
                    (TokenType.SYMBOL, previouslyFound)
                )

            return (RecognizerFlag.REJECTED, None)
        if foundSymbol and not moreSymbols:
            return (RecognizerFlag.RECOGNIZED, (TokenType.SYMBOL, symbol))

        return (RecognizerFlag.WAITING, None)

    def finish(self):
        if self.previouslyFound != None:
            previouslyFound = self.previouslyFound
            self.previouslyFound = None
            return (
                RecognizerFlag.REJECTED,
                (TokenType.SYMBOL, previouslyFound)
            )

        return (RecognizerFlag.REJECTED, None)

def toNumber(char):
    for i, c in enumerate({
        "0": 0,
        "1": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "7": 7,
        "8": 8,
        "9": 9
    }):
        if char == c: return i
    return None

def parseNum(word):
    num = 0
    for c in word:
        i = toNumber(c)
        if i == None: return None
        num = 10*num + i
    return num

class IdentifierRecognizer:
    def __init__(self):
        self.word = ""

    def reset(self):
        self.word = ""

    def reject(self):
        if self.word != "":
            for kw, seq in keywords:
                if self.word == seq: return (
                    RecognizerFlag.REJECTED,
                    (TokenType.KEYWORD, kw)
                )

            if str.isnumeric(self.word[0]):
                num = parseNum(self.word)
                if num == None:
                    return (RecognizerFlag.REJECTED, None)
                else: return (
                    RecognizerFlag.REJECTED, (TokenType.NUMBER, num)
                )

            return (
                RecognizerFlag.REJECTED,
                (TokenType.IDENTIFIER, self.word)
            )
        else:
            return (RecognizerFlag.REJECTED, None)

    def consume(self, char):
        if not str.isalnum(char) and not char == '_':
            return self.reject()

        self.word += char
        return (RecognizerFlag.WAITING, None)

    def finish(self):
        return self.reject()

class ConsumersWrapper:
    def __init__(self, str):
        self.str = str
        self.i = 0
        self.line = 1
        self.col = 1
        self.recognizers = [
            [RecognizerFlag.WAITING, SymbolRecognizer()],
            [RecognizerFlag.WAITING, IdentifierRecognizer()]
        ]

    def resetBeforeToken(self):
        for i in range(len(self.recognizers)):
            self.recognizers[i][0] = RecognizerFlag.WAITING
            self.recognizers[i][1].reset()

    def finishTokenizers(self, start, end):
        for _, recognizer in self.recognizers:
            (_, value) = recognizer.finish()
            if value != None:
                return (value, start, end)
        raise TokenizerError((start, end), "Failed to tokenize this.")

    def nextToken(self):
        # Vrai tant qu'on n'a pas renconté de mot
        whitespace = True
        startpos = None
        reachLineEnd = False
        tokenizeString = False
        builtString = ""

        self.resetBeforeToken()

        # Lit le mot suivant
        while True :
            pos = (self.line, self.col)

            if self.i == len(self.str):
                if tokenizeString:
                    return (
                        (TokenType.STRING, builtString), startpos, pos
                    )
                elif whitespace: return ((TokenType.EOF, None), pos, pos)
                else: return self.finishTokenizers(startpos, pos)

            # Caractère en cours de lecture
            char = self.str[self.i]
            self.i += 1
            self.col += 1

            if reachLineEnd:
                if char == '\n':
                    reachLineEnd = False
                    self.line += 1
                    self.col = 1
                    continue
                else:
                    continue
            if char == '#':
                reachLineEnd = True
                continue

            if tokenizeString:
                if char == '\\':
                    if self.i == len(self.str):
                        raise TokenizerError(
                            (
                                (self.line, self.col-1),
                                (self.line, self.col)
                            ),
                            "Unexpected EOF after '\\'."
                        )

                    escape = self.str[self.i]
                    self.i += 1
                    self.col += 1

                    escape_dict = {
                        '\\': '\\',
                        '"': '"',
                        '\'': '\'',
                        'n': '\n',
                        't': '\t'
                    }

                    if not escape in escape_dict:
                        raise TokenizerError(
                            (pos, (pos[0], pos[1]+2)),
                            "Unknown escape sequence."
                        )

                    builtString += escape_dict[escape]
                elif char == '"':
                    return (
                        (TokenType.STRING, builtString), startpos, pos
                    )
                else:
                    builtString += char
                continue
            else:
                if char == '"':
                    if not whitespace:
                        # On s'occupera de la chaîne de caractère
                        # au prochain appel de "nextToken".
                        self.i -= 1
                        self.col -= 1
                        return self.finishTokenizers(startpos, pos)

                    tokenizeString = True
                    startpos = pos

            if char in [' ', '\t', '\n']:
                if char == '\n':
                    self.line += 1
                    self.col = 1

                if whitespace: continue
                else: return self.finishTokenizers(startpos, pos)

            if whitespace:
                startpos = pos
                pos = (self.line, self.col)

            for i, (flag, recognizer) in enumerate(self.recognizers):
                if flag != RecognizerFlag.WAITING: continue
                (flag, value) = recognizer.consume(char)
                if value != None:
                    if flag == RecognizerFlag.REJECTED:
                        # Le caractère courant peut intéresser
                        # un autre Recognizer.
                        self.i -= 1
                        self.col -= 1
                    return (value, startpos, pos)
                if flag == RecognizerFlag.REJECTED:
                    self.recognizers[i][0] = RecognizerFlag.REJECTED

            whitespace = False

class Tokenizer:
    def __init__(self, str):
        self.wrapper = ConsumersWrapper(str)
        self._current = None
        self._lookahead = None
        self.nextToken()

    def nextToken(self):
        (pair, start, end) = self.wrapper.nextToken()
        token = Token(pair, start, end)
        (self._current, self._lookahead) = (self._lookahead, token)
        return self._current

    def current(self):
        return self._current

    def lookahead(self):
        return self._lookahead
