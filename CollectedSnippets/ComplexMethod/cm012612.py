def iteration_ranges_codegen_header(
        self, entry: IterationRangesRoot, code: IndentedBuffer
    ) -> None:
        x = entry.prefix
        if entry.is_loop:
            code.writeline(f"{entry.name} = {x}offset + {x}base")
        elif entry.grid_dim is None:
            # no need to "{x}offset = "
            code.writeline(f"{entry.name} = {self.iteration_ranges_ranges_code(entry)}")
            code.writeline(f"{x}offset = 0")
        else:
            if entry.tensor_dim is not None:
                line = f"{x}offset + {self.iteration_ranges_ranges_code(entry)}"
            else:
                line = self.iteration_ranges_scalar_code(entry, f"{x}offset")

            block_size = (
                f"{x.upper()}BLOCK" if not self.mix_order_reduction else "RSPLIT_SIZE"
            )
            code.writelines(
                [
                    f"{x}offset = {self.iteration_ranges_get_pid(entry)} * {block_size}",
                    f"{entry.name} = {line}",
                ]
            )
        if self._has_constant_mask(entry):
            code.writeline(self.create_constant_mask(entry))
        elif not (x == "x" and self.mix_order_reduction):
            # mix order reduction should generate xmask inside the loop
            code.writeline(f"{x}mask = {entry.name} < {x}numel")