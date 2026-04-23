def _get_function_impl(self, _converting: set[int]) -> types.FunctionType:
        closure_cells = None
        if self.closure:
            from torch._dynamo.symbolic_convert import InstructionTranslator

            tx = InstructionTranslator.current_tx()
            cells = []

            for cell_var in self.closure.items:  # type: ignore[attr-defined]
                # Get the cell contents from side_effects or pre_existing_contents
                # load_cell will replay the side-effects
                cell_contents = tx.output.side_effects.load_cell(cell_var)

                # Check for self-referential closure (function capturing itself for recursion)
                # For example:
                # def outer():
                #     def helper(n):
                #         if n <= 0:
                #             return 0
                #         return n + helper(n - 1)  # helper calls itself
                #     return helper
                if cell_contents is self:
                    raise ClosureConversionError("self-referential nested function")

                # If the cell contents is a NestedUserFunctionVariable, call get_function
                # directly to properly propagate the _converting set for cycle detection
                if isinstance(cell_contents, NestedUserFunctionVariable):
                    value = cell_contents.get_function(_converting)
                else:
                    value = cell_contents.as_python_constant()
                cells.append(make_cell(value))
            closure_cells = tuple(cells)

        func = types.FunctionType(
            self.code.as_python_constant(),
            self.f_globals,
            self.fn_name.as_python_constant(),
            argdefs=None,
            closure=closure_cells,
        )
        if self.defaults:
            func.__defaults__ = self.defaults.as_python_constant()
        if self.kwdefaults:
            func.__kwdefaults__ = self.kwdefaults.as_python_constant()
        if self.dict_vt and self.dict_vt.contains("__annotations__"):
            annotations = self.dict_vt.getitem("__annotations__").as_python_constant()
            if isinstance(annotations, tuple):
                from itertools import pairwise

                annotations = dict(pairwise(annotations))

            # TypeError: __annotations__ must be set to a dict object
            assert isinstance(annotations, dict)
            func.__annotations__ = annotations
        return func