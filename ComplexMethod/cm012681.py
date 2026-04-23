def uniquify_block_sizes(
        self, code: IndentedBuffer, num_kernel: int, uniquify: list[str]
    ) -> IndentedBuffer:
        if not uniquify:
            return code
        modified = IndentedBuffer(initial_indent=code._indent)
        for line in code._lines:
            if isinstance(line, str) and (blocks := [e for e in uniquify if e in line]):
                modified_line = line
                for block in blocks:
                    modified_line = modified_line.replace(
                        block, f"{block}_{num_kernel}"
                    )
                modified.writeline(modified_line)
            elif isinstance(line, DeferredLine) and (
                blocks := [e for e in uniquify if e in line.line]
            ):
                modified_line = line.line
                for block in blocks:
                    modified_line = modified_line.replace(
                        block, f"{block}_{num_kernel}"
                    )
                new_line = DeferredLine(line.name, modified_line)
                modified.writeline(new_line)
            else:
                modified.writeline(line)
        return modified