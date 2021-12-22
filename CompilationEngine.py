"""This file is part of nand2tetris, as taught in The Hebrew University,
and was written by Aviv Yaish according to the specifications given in  
https://www.nand2tetris.org (Shimon Schocken and Noam Nisan, 2017)
and as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0 
Unported License (https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""

"""
REMEMBER  - EACH FUNCTION **ONLY** ADVANCE IN ITS END!
"""

import typing
import JackTokenizer as JT

dict_tag_open = {"CLASS": "<class>",
                 "KEYWORD": "<keyword> ",
                 "SYMBOL": "<symbol> ",
                 "IDENTIFIER": "<identifier> ",
                 "classVarDec": "<classVarDec> ",
                 "INT_CONST": "<integerConstant> ",
                 "STRING_CONST": "<stringConstant> "}

dict_tag_close = {"CLASS": "</class>",
                  "KEYWORD": " </keyword>",
                  "SYMBOL": " </symbol>",
                  "IDENTIFIER": " </identifier>",
                  "INT_CONST": " </integerConstant>",
                  "STRING_CONST": " </stringConstant>"}

LINE = "\n"

UNARY_OP = ['-', '~', '^', '#']


class CompilationEngine:
    """Gets input from a JackTokenizer and emits its parsed structure into an
    output stream.
    """

    def __init__(self, jack_tokenizer: JT.JackTokenizer,
                 output_stream: typing.TextIO) -> None:
        """
        Creates a new compilation engine with the given input and output. The
        next routine called must be compileClass()
        :param input_stream: The input stream.
        :param output_stream: The output stream.
        """
        self.jt = jack_tokenizer
        self.output_file = output_stream
        self.dict_compile_func = {"class": self.compile_class,
                                  "field": self.compile_class_var_dec,
                                  "static": self.compile_class_var_dec,
                                  "method": self.compile_subroutine,
                                  "function": self.compile_subroutine,
                                  "constructor": self.compile_subroutine,
                                  "var": self.compile_var_dec,
                                  "do": self.compile_do,
                                  "let": self.compile_let,
                                  "if": self.compile_if,
                                  "while": self.compile_while,
                                  "return": self.compile_return}

    def advance(self):
        self.jt.advance()

    def tags(self):
        self.output_file.write(dict_tag_open[self.jt.token_type()] +
                               self.jt.get_cur_token() +
                               dict_tag_close[self.jt.token_type()] + LINE)

    def __check_block(self):
        """Check Next Statement """

        while self.jt.has_more_tokens():
            if self.jt.token_type() == JT.SYMBOL and self.jt.symbol() == "}":
                return
            else:
                if self.jt.token_type() == "KEYWORD":
                    self.dict_compile_func[self.jt.keyword()]()


    def compile_class(self) -> None:
        """Compiles a complete class."""
        self.output_file.write("<class>" + LINE)
        # Writes Class - keyword
        self.tags()
        self.jt.advance()

        # Writes Identifier - className
        self.tags()
        self.jt.advance()

        #Writes { - symbol
        self.tags()
        self.jt.advance()

        self.__check_block()

        #Writes } - symbol
        self.tags()
        self.jt.advance()

        self.output_file.write("</class>" + LINE)

    def compile_class_var_dec(self) -> None:
        """Compiles a static declaration or a field declaration."""
        self.output_file.write("<classVarDec>" + LINE)
        # Writes class variable-static or field - keyword
        self.tags()
        self.jt.advance()
        while self.jt.has_more_tokens():
            if self.jt.symbol() == ";":
                # Writes ; - symbol
                self.tags()
                break
            else:
                self.tags()
                self.jt.advance()

        self.jt.advance()
        self.output_file.write("</classVarDec>\n")

    def compile_subroutine(self) -> None:
        """Compiles a complete method, function, or constructor."""
        # Your code goes here!
        self.output_file.write("<subroutineDec>" + LINE)
        # Writed function/method/constructor - keyword
        self.tags()
        self.jt.advance()

        # Writes return type (keyword)
        self.tags()
        self.jt.advance()

        # Writed func_name (identifier)
        self.tags()
        self.jt.advance()

        # Open bracket of func
        self.tags()
        self.jt.advance()

        self.compile_parameter_list()

        # Closed bracket of func ")"
        self.tags()

        self.advance()
        # OPEN SubroutineBody
        self.output_file.write("<subroutineBody>" + LINE)

        # Open Curly Bracket
        self.tags()
        self.advance()
        while self.jt.get_cur_token() == 'var':
            self.compile_var_dec()
            # self.jt.advance()

        self.compile_statements()

        # Closed Curly Bracket
        self.tags()

        self.jt.advance()
        self.output_file.write("</subroutineBody>" + LINE)

        self.output_file.write("</subroutineDec>" + LINE)


    def compile_parameter_list(self) -> None:
        """Compiles a (possibly empty) parameter list, not including the 
        enclosing "()".
        """
        self.output_file.write("<parameterList>" + LINE)
        if self.jt.get_cur_token() == ")":
            self.output_file.write("</parameterList>" + LINE)
            return

        while self.jt.has_more_tokens():
            if self.jt.symbol() == ")":
                break
            else:
                self.output_file.write(
                    dict_tag_open[f"{self.jt.token_type()}"] +
                    f"{self.jt.get_cur_token()}"
                    f"{dict_tag_close[self.jt.token_type()]}"
                    f"{LINE}")
                self.jt.advance()
        self.output_file.write("</parameterList>" + LINE)

    def compile_var_dec(self) -> None:
        """Compiles a var declaration."""
        self.output_file.write("<varDec>" + LINE)
        # Writes "var"
        self.tags()

        self.jt.advance()
        while self.jt.has_more_tokens():
            if self.jt.symbol() == ";":
                self.tags()
                break
            else:
                self.tags()
                self.jt.advance()

        self.jt.advance()
        self.output_file.write("</varDec>" + LINE)

    def compile_statements(self) -> None:
        """Compiles a sequence of statements, not including the enclosing 
        "{}".
        """
        self.output_file.write("<statements>" + LINE)

        self.__check_block()
        self.output_file.write("</statements>" + LINE)


    def compile_do(self) -> None:
        """Compiles a do statement."""
        self.output_file.write("<doStatement>" + LINE)
        # Write "do"
        self.tags()
        self.advance()

        # Put subroutine or className|varName name - identifier
        self.tags()

        self.advance()
        while self.jt.get_cur_token() == ".":
            # Put '.'
            self.tags()
            self.advance()

            # put subroutineCall - identifier
            self.tags()
            self.advance()

        # Write symbol "("
        self.tags()
        self.advance()

        # if self.jt.get_cur_token() != ")":
        self.compile_expression_list()

        # writes symbol ")"
        self.tags()
        self.advance()

        # writes symbol ";"
        self.tags()
        self.advance()

        self.output_file.write("</doStatement>" + LINE)

    def compile_let(self) -> None:
        """Compiles a let statement."""
        self.output_file.write("<letStatement>" + LINE)
        # Writes 'let' - keyword
        self.tags()

        self.advance()
        # Writes 'varName' - identifier
        self.tags()
        self.advance()

        if self.jt.get_cur_token() == "[":
            # Writes '[' - symbol
            self.tags()
            self.advance()

            self.compile_expression()

            # Writes ']' - symbol
            self.tags()
            self.advance()

        # writes '=' - symbol
        self.tags()
        self.advance()
        self.compile_expression()

        # Writes ';' - symbol
        self.tags()
        self.advance()

        self.output_file.write("</letStatement>" + LINE)

    def compile_while(self) -> None:
        """Compiles a while statement."""
        self.output_file.write("<whileStatement>" + LINE)
        # writes the 'while' itself
        self.tags()
        self.advance()
        # writes '('
        self.tags()
        self.advance()

        self.compile_expression()

        # writes ')'
        self.tags()
        self.advance()
        # writes '{'
        self.tags()
        self.advance()
        self.compile_statements()
        # writes "}"
        self.tags()
        self.advance()
        self.output_file.write("</whileStatement>" + LINE)

    def compile_return(self) -> None:
        """Compiles a return statement."""
        self.output_file.write("<returnStatement>" + LINE)
        self.tags()
        self.jt.advance()
        if self.jt.get_cur_token() != ";":
            self.compile_expression()

        # The ';' symbol
        self.tags()
        self.advance()
        self.output_file.write("</returnStatement>" + LINE)

    def compile_if(self) -> None:
        """Compiles a if statement, possibly with a trailing else clause."""
        self.output_file.write("<ifStatement>" + LINE)
        # writes the 'if' itself
        self.tags()
        self.advance()
        # writes '('
        self.tags()
        self.advance()
        self.compile_expression()

        # writes ')'
        self.tags()
        self.advance()
        # writes '{'
        self.tags()
        self.advance()
        self.compile_statements()
        # writes "}"
        self.tags()
        self.advance()
        if self.jt.get_cur_token() == "else":
            self.compile_else()
        self.output_file.write("</ifStatement>" + LINE)

    def compile_expression(self) -> None:
        """Compiles an expression."""
        self.output_file.write("<expression>" + LINE)
        self.compile_term()
        while self.jt.get_cur_token() != ")" and \
                self.jt.get_cur_token() != "]" and \
                self.jt.get_cur_token() != "," and \
                self.jt.get_cur_token() != ";":
            # OP symbol
            self.tags()
            self.advance()

            self.compile_term()

        self.output_file.write("</expression>" + LINE)

    def compile_term(self) -> None:
        """Compiles a term. 
        This routine is faced with a slight difficulty when
        trying to decide between some of the alternative parsing rules.
        Specifically, if the current token is an identifier, the routing must
        distinguish between a variable, an array entry, and a subroutine call.
        A single look-ahead token, which may be one of "[", "(", or "." suffices
        to distinguish between the three possibilities. Any other token is not
        part of this term and should not be advanced over.
        """
        self.output_file.write("<term>" + LINE)

        # Write the first part of the term
        if self.jt.get_cur_token() in UNARY_OP:
            # Write Unary-OP (symbol)
            self.tags()
            self.advance()
            self.compile_term()

        elif self.jt.get_cur_token() == "(":
            # Write "(" Symbol
            self.tags()
            self.advance()
            self.compile_expression()

            # Write ")" Symbol
            self.tags()
            self.advance()
        else:
            # Write stringConstant\intConstant\keywordConstant\varName\
            # subroutineCall - DO NOT CHANGE HERE!!!
            if self.jt.token_type() == JT.STRING:
                self.output_file.write(dict_tag_open[self.jt.token_type()] +
                                       self.jt.get_cur_token()[1:-1] +
                                       dict_tag_close[self.jt.token_type()]
                                       + LINE)
            else:
                self.tags()
            self.advance()

            if self.jt.get_cur_token() == "[":
                # Write "[" Symbol
                self.tags()
                self.advance()
                self.compile_expression()

                # Write "]" Symbol
                self.tags()
                self.advance()

            elif self.jt.get_cur_token() == "(":
                # Write "(" Symbol
                self.tags()
                self.advance()
                self.compile_expression_list()

                # Write ")" Symbol
                self.tags()
                self.advance()

            elif self.jt.get_cur_token() == ".":
                # Write "." Symbol
                self.tags()
                self.advance()
                # Write "SubroutineName" Identifier
                self.tags()
                self.advance()
                # Write "(" Symbol
                self.tags()
                self.advance()
                self.compile_expression_list()

                # Write ")" Symbol
                self.tags()
                self.advance()

        self.output_file.write("</term>" + LINE)

    def compile_expression_list(self) -> None:
        """Compiles a (possibly empty) comma-separated list of expressions."""

        # WE ALREADY ADVANCED BEFORE AND AFTER!!
        self.output_file.write("<expressionList>" + LINE)
        if self.jt.get_cur_token() != ')':
            self.compile_expression()
            while self.jt.get_cur_token() == ',':
                # Write ','
                self.tags()
                self.advance()

                self.compile_expression()

        # self.jt.advance()
        self.output_file.write("</expressionList>" + LINE)

    def compile_else(self):
        # writes "else"
        self.tags()
        self.advance()
        # writes "{"
        self.tags()
        self.jt.advance()
        self.compile_statements()
        # writes "}"
        self.tags()
        self.jt.advance()
