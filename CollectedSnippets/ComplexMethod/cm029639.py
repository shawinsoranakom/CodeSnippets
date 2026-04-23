def get_methods(self):
        """Return a tuple of methods declared in the class.
        """
        import warnings
        typename = f'{self.__class__.__module__}.{self.__class__.__name__}'
        warnings.warn(f'{typename}.get_methods() is deprecated '
                      f'and will be removed in Python 3.16.',
                      DeprecationWarning, stacklevel=2)

        if self.__methods is None:
            d = {}

            def is_local_symbol(ident):
                flags = self._table.symbols.get(ident, 0)
                return ((flags >> SCOPE_OFF) & SCOPE_MASK) == LOCAL

            for st in self._table.children:
                # pick the function-like symbols that are local identifiers
                if is_local_symbol(st.name):
                    match st.type:
                        case _symtable.TYPE_FUNCTION:
                            d[st.name] = 1
                        case _symtable.TYPE_TYPE_PARAMETERS:
                            # Get the function-def block in the annotation
                            # scope 'st' with the same identifier, if any.
                            scope_name = st.name
                            for c in st.children:
                                if c.name == scope_name and c.type == _symtable.TYPE_FUNCTION:
                                    d[scope_name] = 1
                                    break
            self.__methods = tuple(d)
        return self.__methods