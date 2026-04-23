def numel(self, tx: "InstructionTranslator") -> VariableTracker:
        from .builder import SourcelessBuilder
        from .tensor import SymNodeVariable

        const_result = 1
        # pyrefly: ignore [implicit-any]
        sym_sizes = []

        for v in self.items:
            if v.is_python_constant():
                const_result *= v.as_python_constant()
            else:
                assert isinstance(v, SymNodeVariable), type(v)
                # Delay proxy calls  until we know it will be necessary
                sym_sizes.append(v)

        result = VariableTracker.build(tx, const_result)
        if sym_sizes and const_result == 1:
            # Skip multiplying by 1
            result, *sym_sizes = sym_sizes

        if not sym_sizes or const_result == 0:
            return result

        mul = SourcelessBuilder.create(tx, operator.mul)
        for v in sym_sizes:
            result = mul.call_function(tx, [result, v], {})
        return result