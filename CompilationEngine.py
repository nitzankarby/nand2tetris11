"""This file is part of nand2tetris, as taught in The Hebrew University,
and was written by Aviv Yaish according to the specifications given in  
https://www.nand2tetris.org (Shimon Schocken and Noam Nisan, 2017)
and as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0 
Unported License (https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
from SymbolTable import SymbolTable, ARG, LOCAL, FIELD, STATIC
from JackTokenizer import JackTokenizer, KEYWORD, SYMBOL, IDENTIFIER,\
    INT_CONST, STRING

"""
REMEMBER  - EACH FUNCTION **ONLY** ADVANCE IN ITS END!
"""

import typing
import JackTokenizer as JT
import VMWriter as vm

enum = {
    "constructor": 0,
    "method": 1,
    "function": 2
}
dict_tag_open = {"CLASS": "<class>",
                 "KEYWORD": "<keyword> ",
                 "SYMBOL": "<symbol> ",
                 "IDENTIFIER": "<identifier> ",
                 "classVarDec": "<classVarDec> ",
                 "INT_CONST": "<integerConstant> ",
                 "STRING_CONST": "<stringConstant> "}

un_operation_dict = {
    "-": "NEG",
    "^": "SHIFTLEFT",
    "#": "SHFITRIGHT"
}

operation_dict = {
    "-": "SUB",
    "+": "ADD",
    "=": "EQ",
    ">": "GT",
    "<": "LT",
    "&": "AND",
    "|": "OR"
}

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
        self.vm = vm.VMWriter(output_stream)
        self.class_name = None
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
        self.st = SymbolTable()

    def write_constructor(self):
        arg_num = self.st.var_count(FIELD)
        self.vm.write_push("constant", arg_num)
        self.vm.write_call("Memory.alloc", 1)

    def advance(self):
        self.jt.advance()

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
        self.jt.advance()

        # Writes Identifier - className
        self.class_name = self.jt.get_cur_token()
        self.jt.advance()

        # Writes { - symbol
        self.jt.advance()

        self.__check_block()

        # Writes } - symbol
        self.jt.advance()

    def compile_class_var_dec(self) -> None:
        """Compiles a static declaration or a field declaration."""
        # Writes class variable-static or field - keyword
        obj_kind = self.jt.keyword()  # sets the objects kind
        self.jt.advance()
        obj_type = self.jt.token_type()  # sets the objects type
        while self.jt.has_more_tokens():
            if self.jt.symbol() == ";":
                # Writes ; - symbol
                break
            if self.jt.get_cur_token() == ",":
                continue
            else:
                obj_name = self.jt.get_cur_token()
                self.st.define(obj_name, obj_type, obj_kind)  # writes the object to the symbol table
                self.jt.advance()

        self.jt.advance()

    def compile_subroutine(self) -> None:
        """Compiles a complete method, function, or constructor."""
        # Our code goes here!
        self.st.start_subroutine()
        # Writed function/method/constructor - keyword
        method_type = self.jt.get_cur_token()
        self.jt.advance()

        # Writes return type (keyword)
        self.jt.advance()

        # Writed func_name (identifier)
        func_name = self.jt.get_cur_token()
        self.jt.advance()

        # Open bracket of func
        self.jt.advance()

        if method_type == "constructor":
            self.compile_parameter_list(method_type)
            self.write_constructor()

        elif method_type == "method":
            self.compile_parameter_list(method_type)
            self.vm.write_push("argument", 0)
            self.vm.write_pop("pointer", 0)
        else:
            self.compile_parameter_list(method_type)

        self.advance()
        # OPEN SubroutineBody

        # start func body (passed '{' )
        self.advance()
        while self.jt.get_cur_token() == 'var':
            self.compile_var_dec()
            # self.jt.advance()

        self.compile_statements()

        # Closed Curly Bracket
        self.jt.advance()

    def compile_parameter_list(self, calli_type) -> None:
        """Compiles a (possibly empty) parameter list, not including the 
        enclosing "()".
        """
        if calli_type == "method":  # TODO: Daniels elephant tail.
            self.st.define("this", self.class_name, ARG)
        if self.jt.get_cur_token() == ")":
            return

        while self.jt.has_more_tokens():
            if self.jt.symbol() == ")":
                break
            else:
                if self.jt.get_cur_token() == ",":
                    continue
                else:
                    token_type = self.jt.get_cur_token()
                    self.jt.advance()
                    token_name = self.jt.get_cur_token()
                    self.st.define(token_name, token_type, ARG)
                self.jt.advance()

    def compile_var_dec(self) -> None:
        """Compiles a var declaration."""
        # token = "var"
        self.jt.advance()
        while self.jt.has_more_tokens():
            if self.jt.symbol() == ";":
                break
            elif self.jt.get_cur_token() == ",":
                continue
            else:
                token_type = self.jt.token_type()
                self.advance()
                token_name = self.jt.get_cur_token()
                self.st.define(token_name, token_type, LOCAL)
                self.advance()
        self.jt.advance()

    def compile_statements(self) -> None:
        """Compiles a sequence of statements, not including the enclosing 
        "{}".
        """
        self.__check_block()

    def compile_do(self) -> None:
        """Compiles a do statement."""
        # Write "do"
        self.advance()

        # Put subroutine or className|varName name - identifier
        caller_name = self.jt.get_cur_token()
        self.advance()
        while self.jt.get_cur_token() == ".":
            # Put '.'
            caller_name += "."
            self.advance()

            # put subroutineCall - identifier
            caller_name += self.jt.get_cur_token()
            self.advance()

        # Write symbol "("
        self.advance()

        # if self.jt.get_cur_token() != ")":
        param_count = self.compile_expression_list()

        # writes symbol ")"
        self.advance()
        self.vm.write_call(caller_name, param_count)
        # writes symbol ";"
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
        self.compile_term()
        while self.jt.get_cur_token() != ")" and \
                self.jt.get_cur_token() != "]" and \
                self.jt.get_cur_token() != "," and \
                self.jt.get_cur_token() != ";":
            # OP symbol
            self.tags()
            self.advance()

            self.compile_term()

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
        # Write the first part of the term
        if self.jt.get_cur_token() in UNARY_OP:
            # Write Unary-OP (symbol)
            unary_op = self.jt.get_cur_token()
            self.advance()
            self.compile_term()
            self.vm.write_arithmetic(un_operation_dict[unary_op])

        elif self.jt.get_cur_token() == "(":
            # Write "(" Symbol
            self.advance()
            self.compile_expression()
            # Write ")" Symbol
            self.advance()
        else:
            # Write stringConstant\intConstant\keywordConstant\varName\
            # subroutineCall - DO NOT CHANGE HERE!!!
            if self.jt.token_type() == JT.STRING:
                self.output_file.write(dict_tag_open[self.jt.token_type()] +
                                       self.jt.get_cur_token()[1:-1] +
                                       dict_tag_close[self.jt.token_type()]
                                       + LINE)                              #TODO: THE BIGGEST ELEPHANT TAIL
            else:
                # self.tags()
                type_term = self.jt.token_type()
                cur_token = self.jt.get_cur_token()
                if type_term == INT_CONST:
                    self.vm.write_push("constant",self.jt.get_cur_token())
                    self.advance()
                elif type_term == IDENTIFIER:
                    self.advance()
                    if cur_token != "(" or cur_token != "." or \
                            cur_token != "[":
                        self.vm.write_push(self.st.kind_of(cur_token),
                                           self.st.index_of(cur_token))
                else:
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

    def compile_expression_list(self):
        """Compiles a (possibly empty) comma-separated list of expressions."""
        param_count = 0
        if self.jt.get_cur_token() != ')':
            self.compile_expression()
            while self.jt.get_cur_token() == ',':
                # Write ','
                self.advance()

                self.compile_expression()

        # self.jt.advance()
        return param_count

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
