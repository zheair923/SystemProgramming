import re

from processlib.Token import ScannerToken, TokenType


class Scanner:
    TOKEN_TYPES = [
        TokenType('KEYWORD', r'for|return'),
        TokenType('NUMBER', r'[0-9]+'),
        TokenType('ASSIGN', r'='),
        TokenType('END', r';'),
        TokenType('SYMBOL', r'[(){}]'),
        TokenType('ID', r'[A-Za-z_][A-Za-z0-9_]*'),
        TokenType('UnaryOP', r'--|\+\+'),
        TokenType('OP', r'[+\-*/]'),
        TokenType('COND', r'==|!=|<=|>=|<|>'),
        TokenType('NEWLINE', r'\r\n|\n'),
        TokenType('SPACE', r'[ \t]+'),
        TokenType('OTHER', r'.')
    ]
    TOKEN_REGEX = '|'.join(('(?P<{}>{})'.format(token_kind.name, token_kind.regex) for token_kind in TOKEN_TYPES))

    def __init__(self) -> None:
        super().__init__()
        self.content = None
        self.context = None
        self.next_token: ScannerToken = None
        self.ended = False

    def _generator(self, regex: str, content: str) -> ScannerToken:
        line = 1
        next_token_pos = 1
        for find in re.finditer(regex, content):
            kind = find.lastgroup
            value = find.group(kind)
            if kind == 'NEWLINE':
                line += 1
                next_token_pos = 1
            else:
                next_token_pos += len(value)

            if kind == 'SPACE' or kind == 'NEWLINE':
                continue
            if kind == 'OTHER':
                raise RuntimeError('未知類型token:{}'.format(value))
            yield ScannerToken(next(token_type for token_type in Scanner.TOKEN_TYPES if token_type.name == kind),
                               value, line, next_token_pos - len(value))

    def is_next(self, token: str) -> bool:
        if self.next_token.type.name != token and token != self.next_token.value:
            return False
        elif self.ended is True:
            raise RuntimeError('已經讀到文件結尾了')
        return True

    def get_next(self, token: str) -> ScannerToken:
        try:
            if self.next_token.type.name != token and token != self.next_token.value:
                raise RuntimeError('預期{}但得到{}\n{}\n{}^'.format(token,
                                                               self.next_token,
                                                               self.content.split('\n')[self.next_token.line - 1],
                                                               ' ' * (self.next_token.position - 1)))
            elif self.ended is True:
                raise RuntimeError('已經讀到文件結尾了')

            token = self.next_token
            self.next_token = next(self.context)

        except StopIteration:
            self.ended = True
        return token

    def is_end(self):
        return self.ended

    def set(self, content):
        self.content = content
        self.context = self._generator(Scanner.TOKEN_REGEX, content)
        self.next_token: ScannerToken = next(self.context)
        self.ended = False


class BNFScanner:

    def __init__(self) -> None:
        super().__init__()
        self.context = None

    def _generator(self, content):
        request, step_mode = None, None
        result = None
        end = False
        while content != '' or end:
            request, step_mode = yield result
            if end:
                return
            find = re.match(request, content)
            if find is None:
                result = None
                continue

            result = find.group(0)
            if step_mode:
                content = content[find.end():]
                if len(content) is 0:
                    end = True

    def is_next(self, request, re_mode=False):
        if self.is_end():
            raise RuntimeError('End of the scanner')
        if re_mode is False:
            request = re.escape(request)
        result = self.context.send((request, False))
        if result is None:
            return False
        return True

    def get_next(self, request, re_mode=False):
        if self.is_end():
            raise RuntimeError('End of the scanner')
        if re_mode is False:
            request = re.escape(request)
        result = self.context.send((request, True))
        if result is None:
            return None
        return result

    def is_end(self):
        try:
            self.context.send(('', False))
        except StopIteration:
            return True
        return False

    def set(self, content):
        self.context = self._generator(content)
        next(self.context)


if __name__ == '__main__':
    scanner = BNFScanner()
    scanner.set('asd 123 asf')
    print(scanner.is_next('asd'))
    print(scanner.is_next('123'))
    print(scanner.get_next('123'))
    print(scanner.get_next('asd'))
    print(scanner.get_next(' '))
    print(scanner.get_next('123'))
    print(scanner.get_next(' '))
    print(scanner.get_next('asf'))
    print(scanner.is_end())

    scanner.set('asd 123 asf')
    print(scanner.is_next('asd'))
    print(scanner.is_next('123'))
    print(scanner.get_next('123'))
    print(scanner.get_next('[a-z]*', re_mode=True))
    print(scanner.get_next(' '))
    print(scanner.get_next('[0-9]*', re_mode=True))
    print(scanner.get_next(' '))
    print(scanner.get_next('[a-z]*', re_mode=True))
    print(scanner.is_end())
