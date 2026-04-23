def _push_defined_outputs(self) -> None:
        defined_output = ""
        for output in self.outputs:
            if output.in_local and not output.memory_offset and not output.item.peek:
                defined_output = output.name
        if not defined_output:
            return
        self.clear_inputs(f"when output '{defined_output}' is defined")
        undefined = ""
        for out in self.outputs:
            if out.in_local:
                if undefined:
                    f"Locals not defined in stack order. "
                    f"Expected '{undefined}' to be defined before '{out.name}'"
            else:
                undefined = out.name
        while len(self.outputs) > self.peeks and not self.needs_defining(self.outputs[self.peeks]):
            out = self.outputs.pop(self.peeks)
            self.stack.push(out)