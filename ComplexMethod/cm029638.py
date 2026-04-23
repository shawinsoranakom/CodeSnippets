def get_type(self):
        """Return the type of the symbol table.

        The value returned is one of the values in
        the ``SymbolTableType`` enumeration.
        """
        if self._table.type == _symtable.TYPE_MODULE:
            return SymbolTableType.MODULE
        if self._table.type == _symtable.TYPE_FUNCTION:
            return SymbolTableType.FUNCTION
        if self._table.type == _symtable.TYPE_CLASS:
            return SymbolTableType.CLASS
        if self._table.type == _symtable.TYPE_ANNOTATION:
            return SymbolTableType.ANNOTATION
        if self._table.type == _symtable.TYPE_TYPE_ALIAS:
            return SymbolTableType.TYPE_ALIAS
        if self._table.type == _symtable.TYPE_TYPE_PARAMETERS:
            return SymbolTableType.TYPE_PARAMETERS
        if self._table.type == _symtable.TYPE_TYPE_VARIABLE:
            return SymbolTableType.TYPE_VARIABLE
        assert False, f"unexpected type: {self._table.type}"