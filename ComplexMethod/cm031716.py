def parse_cloned_function(self, names: FunctionNames, existing: str) -> None:
        full_name, c_basename = names
        fields = [x.strip() for x in existing.split('.')]
        function_name = fields.pop()
        module, cls = self.clinic._module_and_class(fields)
        parent = cls or module

        for existing_function in parent.functions:
            if existing_function.name == function_name:
                break
        else:
            print(f"{cls=}, {module=}, {existing=}", file=sys.stderr)
            print(f"{(cls or module).functions=}", file=sys.stderr)
            fail(f"Couldn't find existing function {existing!r}!")

        fields = [x.strip() for x in full_name.split('.')]
        function_name = fields.pop()
        module, cls = self.clinic._module_and_class(fields)

        overrides: dict[str, Any] = {
            "name": function_name,
            "full_name": full_name,
            "module": module,
            "cls": cls,
            "c_basename": c_basename,
            "docstring": "",
        }
        if not (existing_function.kind is self.kind and
                existing_function.coexist == self.coexist):
            # Allow __new__ or __init__ methods.
            if existing_function.kind.new_or_init:
                overrides["kind"] = self.kind
                # Future enhancement: allow custom return converters
                overrides["return_converter"] = CReturnConverter()
            else:
                fail("'kind' of function and cloned function don't match! "
                     "(@classmethod/@staticmethod/@coexist)")
        function = existing_function.copy(**overrides)
        self.function = function
        self.block.signatures.append(function)
        (cls or module).functions.append(function)
        self.next(self.state_function_docstring)