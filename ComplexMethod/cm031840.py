def close_inputs(self, out: CWriter) -> None:

        tmp_defined = False
        def close_named(close: str, name: str, overwrite: str) -> None:
            nonlocal tmp_defined
            if overwrite:
                if not tmp_defined:
                    out.emit("_PyStackRef ")
                    tmp_defined = True
                out.emit(f"tmp = {name};\n")
                out.emit(f"{name} = {overwrite};\n")
                self.stack.save_variables(out)
                out.emit(f"{close}(tmp);\n")
            else:
                out.emit(f"{close}({name});\n")

        def close_variable(var: Local, overwrite: str) -> None:
            nonlocal tmp_defined
            close = "PyStackRef_CLOSE"
            if "null" in var.name:
                close = "PyStackRef_XCLOSE"
            var.memory_offset = None
            self.save(out)
            out.start_line()
            if var.size:
                if var.size == "1":
                    close_named(close, f"{var.name}[0]", overwrite)
                else:
                    if overwrite and not tmp_defined:
                        out.emit("_PyStackRef tmp;\n")
                        tmp_defined = True
                    out.emit(f"for (int _i = {var.size}; --_i >= 0;) {{\n")
                    close_named(close, f"{var.name}[_i]", overwrite)
                    out.emit("}\n")
            else:
                close_named(close, var.name, overwrite)
            self.reload(out)

        self.clear_dead_inputs()
        if not self.inputs:
            return
        lowest = self.inputs[0]
        output: Local | None = None
        for var in self.outputs:
            if var.is_array():
                if len(self.inputs) > 1:
                    raise StackError("Cannot call DECREF_INPUTS with array output and more than one input")
                output = var
            elif var.in_local:
                if output is not None:
                    raise StackError("Cannot call DECREF_INPUTS with more than one live output")
                output = var
        if output is not None:
            if output.is_array():
                assert len(self.inputs) == 1
                self.stack.drop(self.inputs[0].item, False)
                self.stack.push(output)
                self.stack.flush(out)
                close_variable(self.inputs[0], "")
                self.stack.drop(output.item, self.check_liveness)
                self.inputs = []
                return
            if var_size(lowest.item) != var_size(output.item):
                raise StackError("Cannot call DECREF_INPUTS with live output not matching first input size")
            self.stack.flush(out)
            lowest.in_local = True
            close_variable(lowest, output.name)
            assert lowest.memory_offset is not None
        for input in reversed(self.inputs[1:]):
            close_variable(input, "PyStackRef_NULL")
        if output is None:
            close_variable(self.inputs[0], "PyStackRef_NULL")
        for input in reversed(self.inputs[1:]):
            input.kill()
            self.stack.drop(input.item, self.check_liveness)
        if output is None:
            self.inputs[0].kill()
        self.stack.drop(self.inputs[0].item, False)
        output_in_place = self.outputs and output is self.outputs[0] and lowest.memory_offset is not None
        if output_in_place:
            output.memory_offset = lowest.memory_offset  # type: ignore[union-attr]
        else:
            self.stack.flush(out)
        if output is not None:
            self.stack.push(output)
        self.inputs = []
        if output_in_place:
            self.stack.flush(out)
        if output is not None:
            output = self.stack.pop(output.item, out)