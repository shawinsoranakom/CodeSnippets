def resolve_return_converter(
        self, full_name: str, forced_converter: str
    ) -> CReturnConverter:
        if forced_converter:
            if self.kind in {GETTER, SETTER}:
                fail(f"@{self.kind.name.lower()} method cannot define a return type")
            if self.kind is METHOD_INIT:
                fail("__init__ methods cannot define a return type")
            ast_input = f"def x() -> {forced_converter}: pass"
            try:
                module_node = ast.parse(ast_input)
            except SyntaxError:
                fail(f"Badly formed annotation for {full_name!r}: {forced_converter!r}")
            function_node = module_node.body[0]
            assert isinstance(function_node, ast.FunctionDef)
            try:
                name, legacy, kwargs = self.parse_converter(function_node.returns)
                if legacy:
                    fail(f"Legacy converter {name!r} not allowed as a return converter")
                if name not in return_converters:
                    fail(f"No available return converter called {name!r}")
                return return_converters[name](**kwargs)
            except ValueError:
                fail(f"Badly formed annotation for {full_name!r}: {forced_converter!r}")

        if self.kind in {METHOD_INIT, SETTER}:
            return int_return_converter()
        return CReturnConverter()