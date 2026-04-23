def signature_str_pyi_vararg(self, *, skip_outputs: bool = False) -> str | None:
        # only pyi uses vararg signatures
        args = self.arguments(skip_outputs=skip_outputs)
        schema_formals: list[str] = [
            a.argument_str_pyi(method=self.method) for a in args
        ]
        # vararg only applies to pyi signatures. vararg variants are not generated for all signatures
        num_args = self.arguments_count()
        if num_args == 0:
            return None

        num_positionalargs = len(self.input_args)

        vararg_type = args[0].type
        if not (
            isinstance(vararg_type, ListType)
            and str(vararg_type.elem) in ["int", "SymInt"]
            and num_positionalargs == 1
        ):
            return None

        # Below are the major changes in vararg vs. regular pyi signatures
        # vararg signatures also omit the asterix
        if not isinstance(vararg_type, ListType):
            raise AssertionError(f"Expected ListType, got {type(vararg_type)}")
        schema_formals[0] = (
            "*" + args[0].name + ": " + argument_type_str_pyi(vararg_type.elem)
        )

        returns_str = returns_str_pyi(self)
        # pyi also includes self (with no typing/defaults) for methods
        if self.method:
            schema_formals.insert(0, "self")
        return format_function_signature(self.name, schema_formals, returns_str)