def convert_to_sympy_symbols(self, typ: Any) -> Any:
        """
        Replace all unknown types with fresh type variables.
        """
        if isinstance(typ, Var):
            return sympy.symbols(str(typ))
        elif isinstance(typ, TensorType):
            new_args = [self.convert_to_sympy_symbols(a) for a in typ.__args__]
            return TensorType(tuple(new_args))
        elif isinstance(typ, list):
            return [self.convert_to_sympy_symbols(t) for t in typ]
        elif isinstance(typ, tuple):
            return (self.convert_to_sympy_symbols(t) for t in typ)
        else:
            return typ