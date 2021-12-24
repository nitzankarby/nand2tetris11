"""This file is part of nand2tetris, as taught in The Hebrew University,
and was written by Aviv Yaish according to the specifications given in  
https://www.nand2tetris.org (Shimon Schocken and Noam Nisan, 2017)
and as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0 
Unported License (https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing

STATIC = "static"
FIELD = "this"  # todo: the same elephant
ARG = "argument"
LOCAL = "local"


class SymbolTable:
    """A symbol table that associates names with information needed for Jack
    compilation: type, kind and running index. The symbol table has two nested
    scopes (class/subroutine).
    """

    def __init__(self) -> None:
        """Creates a new empty symbol table."""
        self.kind_dict = {
            STATIC: 0,
            FIELD: 0,
            ARG: 0,
            LOCAL: 0
        }
        self.class_dict = {}  # keys : names , values : array of [type, kind, index]
        self.subroutine_dict = {}

    def start_subroutine(self) -> None:
        """Starts a new subroutine scope (i.e., resets the subroutine's 
        symbol table).
        """
        self.kind_dict[ARG], self.kind_dict[LOCAL] = 0, 0
        self.subroutine_dict = {}

    def define(self, name: str, type: str, kind: str) -> None:
        """Defines a new identifier of a given name, type and kind and assigns 
        it a running index. "STATIC" and "FIELD" identifiers have a class scope, 
        while "ARG" and "VAR" identifiers have a subroutine scope.

        Args:
            name (str): the name of the new identifier.
            type (str): the type of the new identifier.
            kind (str): the kind of the new identifier, can be:
            "STATIC", "FIELD", "ARG", "VAR".
        """
        self.kind_dict[kind] += 1
        if type in [STATIC, FIELD]:
            self.class_dict[name] = [type, kind, self.kind_dict[kind]]
        else:
            self.subroutine_dict[name] = [type, kind, self.kind_dict[kind]]

    def var_count(self, kind: str) -> int:
        """
        Args:
            kind (str): can be "STATIC", "FIELD", "ARG", "VAR".

        Returns:
            int: the number of variables of the given kind already defined in 
            the current scope.
        """
        return self.kind_dict[kind]

    def kind_of(self, name: str):
        """
        Args:
            name (str): name of an identifier.

        Returns:
            str: the kind of the named identifier in the current scope, or None
            if the identifier is unknown in the current scope.
        """
        return self.get_value(name, 1)

    def type_of(self, name: str):
        """
        Args:
            name (str):  name of an identifier.

        Returns:
            str: the type of the named identifier in the current scope.
        """
        return self.get_value(name, 0)

    def index_of(self, name: str) -> int:
        """
        Args:
            name (str):  name of an identifier.

        Returns:
            int: the index assigned to the named identifier.
        """
        return self.get_value(name, 2)

    def get_value(self, name, value_index):
        """
        Args:
            name(str):  name of an identifier.
            value_index(int): location of desired data in the dictionary index
        returns:
            data (str) as located in the dictionary
        """
        if self.class_dict.get(name):
            return self.class_dict[name][value_index]
        elif self.subroutine_dict.get(name):
            return self.subroutine_dict[name][value_index]
        else:
            return None
