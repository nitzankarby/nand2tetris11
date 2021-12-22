"""This file is part of nand2tetris, as taught in The Hebrew University,
and was written by Aviv Yaish according to the specifications given in  
https://www.nand2tetris.org (Shimon Schocken and Noam Nisan, 2017)
and as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0 
Unported License (https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import re
import typing

KEYWORD_PATTERN = 'class|constructor|function|method|field|static|var|int|' \
                  'char|boolean|void|true|false|null|this|let|do|' \
                  'if|else|while|return'

SYMBOL_PATTERN = '\{|\}|\(|\)|\[|\]|\.|\,|\;|\+|\-|\/|\*|\&|\||' \
                 '\<|\>|\=|\~|\^|\#'
# DIGIT_PATTERN = '[0-9]{0,5}'
DIGIT_PATTERN = '\d+'
STRING_PATTERN = "\".*\""
IDENTIFIER_PATTERN = "\w+"

KEYWORD, SYMBOL, IDENTIFIER, INT_CONST, STRING = "KEYWORD", \
                                                 "SYMBOL", \
                                                 "IDENTIFIER", \
                                                 "INT_CONST", \
                                                 "STRING_CONST"


class JackTokenizer:
    """Removes all comments from the input stream and breaks it
    into Jack language tokens, as specified by the Jack grammar.
    """

    def __init__(self, input_stream: typing.TextIO) -> None:
        """Opens the input stream and gets ready to tokenize it.

        Args:
            input_stream (typing.TextIO): input stream.
        """
        self.input_lines = input_stream.read().splitlines()
        self.token_counter = 0
        self.parsed_text = self.clean_input()
        self.len = len(self.parsed_text)

    def has_more_tokens(self) -> bool:
        """Do we have more tokens in the input?

        Returns:
            bool: True if there are more tokens, False otherwise.
        """
        return self.len > self.token_counter

    def advance(self) -> None:
        """Gets the next token from the input and makes it the current token. 
        This method should be called if has_more_tokens() is true. 
        Initially there is no current token.
        """
        self.token_counter += 1

    def token_type(self) -> str:
        """
        Returns:
            str: the type of the current token, can be
            "KEYWORD", "SYMBOL", "IDENTIFIER", "INT_CONST", "STRING_CONST"
        """
        token = self.parsed_text[self.token_counter]
        if re.fullmatch(KEYWORD_PATTERN, token):
            return KEYWORD
        elif re.match(SYMBOL_PATTERN, token):
            return SYMBOL
        elif re.match(DIGIT_PATTERN, token):
            return INT_CONST
        elif re.match(STRING_PATTERN, token):
            return STRING
        else:
            return IDENTIFIER

    def keyword(self) -> str:
        """
        Returns:
            str: the keyword which is the current token.
            Should be called only when token_type() is "KEYWORD".
            Can return "CLASS", "METHOD", "FUNCTION", "CONSTRUCTOR", "INT", 
            "BOOLEAN", "CHAR", "VOID", "VAR", "STATIC", "FIELD", "LET", "DO", 
            "IF", "ELSE", "WHILE", "RETURN", "TRUE", "FALSE", "NULL", "THIS"
        """
        return self.parsed_text[self.token_counter]

    def symbol(self) -> str:
        """
        Returns:
            str: the character which is the current token.
            Should be called only when token_type() is "SYMBOL".
        """
        return self.parsed_text[self.token_counter]

    def identifier(self) -> str:
        """
        Returns:
            str: the identifier which is the current token.
            Should be called only when token_type() is "IDENTIFIER".
        """
        return self.parsed_text[self.token_counter]

    def int_val(self) -> int:
        """
        Returns:
            str: the integer value of the current token.
            Should be called only when token_type() is "INT_CONST".
        """
        return self.parsed_text[self.token_counter]

    def string_val(self) -> str:
        """
        Returns:
            str: the string value of the current token, without the double 
            quotes. Should be called only when token_type() is "STRING_CONST".
        """
        return self.parsed_text[self.token_counter]

    def clean_input(self):
        array = []
        line_idx = 0
        while line_idx < len(self.input_lines):
            line = self.input_lines[line_idx]
            if line[0:2] == "/*":
                while "*/" not in line:
                    line_idx += 1
                    line = self.input_lines[line_idx]
                line_idx += 1
                continue
            if len(line) == 0 or line[0] == "*" or line[0:2] == "//":
                line_idx += 1
                continue

            else:
                # line = line.strip()
                line = re.sub("/\*.*\*/", "", line).strip()
                if line[0:2] == "/*":
                    while "*/" not in line:
                        line_idx += 1
                        line = self.input_lines[line_idx]
                    line_idx += 1
                    continue
                if len(line) == 0 or line[0] == "*" or \
                        line[0:2] == "//" or line[0:2] == "/*":
                    line_idx += 1
                    continue
                idx_matcher_quote = re.search("(\")", line)
                idx = self.string_comment_checker(line)
                # idx_matcher = re.search("(//|/\*)",
                #                         line)  # TODO : ADD OPTION */ and
                #               than it will start right after it! IMPORTANT
                # idx = len(line)
                # if idx_matcher != None:
                #     idx = idx_matcher.start()
                temp = [x for x in re.findall(r'({}|{}|{}|{}|{})'.format(
                    IDENTIFIER_PATTERN, DIGIT_PATTERN, STRING_PATTERN,
                    SYMBOL_PATTERN, KEYWORD_PATTERN), line[:idx])]
                temp2 = []
                for i in range(len(temp)):
                    if temp[i] == "<":
                        temp2.append("&lt;")
                    elif temp[i] == ">":
                        temp2.append("&gt;")
                    # elif re.match(STRING_PATTERN,temp[i]):
                    # temp2.append(temp[i][1:-1])
                    elif temp[i] == "&":
                        temp2.append("&amp;")
                    else:
                        temp2.append(temp[i])

                array += [t for t in temp2 if len(t) > 0]
                line_idx += 1
        # self.len = len(self.parsed_text)
        return array

    def get_cur_token(self):
        """ Return current token"""
        return self.parsed_text[self.token_counter]

    def string_comment_checker(self, line):
        all_quotes = [x.start() for x in re.finditer("\"", line)]
        all_backslash = [x.start() for x in re.finditer("//|/\*", line)]
        if len(all_backslash) == 0:
            return len(line)

        if len(all_quotes) == 0:
            return all_backslash[0]

        i = 0
        j = 0
        while i < len(all_quotes) and j < len(all_backslash):
            while all_quotes[i] < all_backslash[j] < all_quotes[i + 1]:
                j += 1
                if j >= len(all_backslash):
                    break
            if j >= len(all_backslash):
                break
            i += 2

        if j < len(all_backslash):
            return all_backslash[j]

        if i < len(all_quotes):
            return len(line)
