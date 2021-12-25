"""This file is part of nand2tetris, as taught in The Hebrew University,
and was written by Aviv Yaish according to the specifications given in  
https://www.nand2tetris.org (Shimon Schocken and Noam Nisan, 2017)
and as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0 
Unported License (https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
from SymbolTable import SymbolTable, ARG, LOCAL, FIELD, STATIC
from JackTokenizer import JackTokenizer, KEYWORD, SYMBOL, IDENTIFIER, \
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
        self.if_counter = 0
        self.while_count = 0
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
        self.math_operation_dict = {
            "*": "Math.multiply",
            "/": "Math.divide"
        }

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
        # Written function/method/constructor - keyword
        method_type = self.jt.get_cur_token()
        self.jt.advance()

        # Writes return type (keyword)
        self.jt.advance()

        # Written func_name (identifier)
        func_name = self.class_name + "." + self.jt.get_cur_token()
        self.jt.advance()

        # Open bracket of func
        self.jt.advance()
        n_args = self.compile_parameter_list(method_type)
        self.vm.write_function(func_name, n_args)

        if method_type == "constructor":
            self.write_constructor()

        elif method_type == "method":
            self.vm.write_push("argument", 0)
            self.vm.write_pop("pointer", 0)

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

    def compile_parameter_list(self, calli_type):
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
        return self.st.var_count(ARG)

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

    def compile_let(self) -> None:
        """Compiles a let statement."""
        # 'let' - keyword
        self.advance()
        # 'varName' - identifier
        var_name = self.jt.get_cur_token()
        self.advance()

        if self.jt.get_cur_token() == "[":
            #  '[' - symbol
            self.advance()
            self.compile_expression()
            #  ']' - symbol
            self.advance()
        # navigation to var pointer plus the location (memory navigation)
        self.vm.write_push(self.st.kind_of(var_name),
                           self.st.index_of(var_name))  # assuming the last pushed value is an int constant
        self.output_file.write(operation_dict["+"])  # getting the right location
        #  '=' - symbol
        self.advance()
        self.compile_expression()
        self.vm.write_pop("temp", 0)
        self.vm.write_pop("pointer", 1)
        self.vm.write_push("temp", 0)
        self.vm.write_pop("that", 0)
        # end of line (;)
        self.advance()

    def compile_while(self) -> None:
        """Compiles a while statement."""
        self.while_count += 1
        #  the 'while' itself
        self.advance()
        #  '('
        self.advance()
        self.vm.write_label(f"while_label.{self.while_count}")
        self.compile_expression()
        self.vm.write_arithmetic("NEG")
        self.vm.write_if(f"while_label_2.{self.while_count}")
        # writes ')'
        self.advance()
        # writes '{'
        self.advance()
        self.compile_statements()
        self.vm.write_goto(f"while_label.{self.while_count}")
        # writes "}"
        self.advance()
        self.vm.write_label(f"while_label_2.{self.while_count}")

    def compile_return(self) -> None:
        """Compiles a return statement."""
        self.jt.advance()
        if self.jt.get_cur_token() != ";":
            self.compile_expression()
            self.vm.write_return()
        else:
            self.vm.write_push("constant", 0)
            self.vm.write_return()
            self.vm.write_pop("temp", 0)
        # The ';' symbol
        self.advance()

    def compile_if(self) -> None:
        """Compiles a if statement, possibly with a trailing else clause."""
        self.if_counter += 1
        #  the 'if' itself
        self.advance()
        #  '('
        self.advance()
        self.compile_expression()
        self.vm.write_arithmetic("NEG")
        self.vm.write_if(f"label.{self.if_counter}")
        #  ')'
        self.advance()
        #  '{'
        self.advance()
        self.compile_statements()
        #  "}"
        self.advance()
        self.vm.write_goto(f"label_2.{self.if_counter}")
        self.vm.write_label(f"label.{self.if_counter}")
        if self.jt.get_cur_token() == "else":
            self.compile_else()

        self.vm.write_label(f"label_2.{self.if_counter}")

    def compile_expression(self) -> None:
        """Compiles an expression."""
        self.compile_term()
        while self.jt.get_cur_token() != ")" and \
                self.jt.get_cur_token() != "]" and \
                self.jt.get_cur_token() != "," and \
                self.jt.get_cur_token() != ";":
            # OP symbol
            if self.jt.get_cur_token() in self.math_operation_dict.keys():
                self.vm.write_call(self.math_operation_dict[self.jt.get_cur_token()], 2)
            else:
                self.vm.write_arithmetic(operation_dict[self.jt.get_cur_token()])
            self.advance()
            # make sure a push is happening
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
        # TODO: in case of info loss. may need to add advance calls
        type_term = self.jt.token_type()
        cur_token = self.jt.get_cur_token()
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

        else:
            # Write stringConstant\intConstant\keywordConstant\varName\
            if self.jt.token_type() == JT.STRING:
                cur_string = self.jt.get_cur_token()[1:-1]
                self.vm.write_push("constant", len(cur_string))
                self.vm.write_call("String.new", 1)
                for i in range(len(cur_string)):
                    self.vm.write_push("constant", ord(cur_string[i]))
                    self.vm.write_call("String.appendChar", 2)
                    # ToDo: daniel will check the code block in his free time
            elif type_term == INT_CONST:
                self.vm.write_push("constant", self.jt.get_cur_token())

            elif type_term == KEYWORD:
                if cur_token == "true":
                    self.vm.write_push("constant", 1)
                    self.vm.write_arithmetic("NEG")
                elif cur_token == "this":
                    self.vm.write_push("pointer", 0)
                else:
                    self.vm.write_push("constant", 0)

            elif type_term == IDENTIFIER:
                self.advance()  # TODO: might need to go back one token
                if cur_token != "(" or cur_token != "." or \
                        cur_token != "[":
                    self.vm.write_push(self.st.kind_of(cur_token),
                                       self.st.index_of(cur_token))
                    return

                elif self.jt.get_cur_token() == "[":
                    # Write "[" Symbol
                    self.advance()
                    self.compile_expression()
                    self.vm.write_push(self.st.kind_of(cur_token), self.st.index_of(cur_token))
                    self.vm.write_pop("pointer", 1)
                    self.vm.write_push("that", 0)
                    # Write "]" Symbol

                elif self.jt.get_cur_token() == "(":
                    # Write "(" Symbol
                    self.advance()
                    n_args = self.compile_expression_list()
                    self.vm.write_call(cur_token, n_args)
                    # Write ")" Symbol

                elif self.jt.get_cur_token() == ".":
                    # Write "." Symbol
                    def create_call(cur_token):
                        cur_token += "."
                        self.advance()
                        cur_token += self.jt.get_cur_token()
                        # Write "SubroutineName" Identifier
                        self.advance()
                        return cur_token

                    cur_token = create_call(cur_token)
                    while self.jt.get_cur_token() == ".":
                        cur_token = create_call(cur_token)
                    # Write "(" Symbol
                    self.advance()
                    n_args = self.compile_expression_list()
                    self.vm.write_call(cur_token, n_args)
                    # Write ")" Symbol

        self.advance()

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
        self.advance()
        # writes "{"
        self.jt.advance()
        self.compile_statements()
        # writes "}"
        self.jt.advance()
