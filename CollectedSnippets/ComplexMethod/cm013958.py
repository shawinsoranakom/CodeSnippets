def extract_pattern(fn: Callable[..., Any]) -> tuple[list[str], str | None]:
        """Extract (pre_store_ops, post_store_op) from comprehension bytecode."""
        target_line = list(dis.findlinestarts(fn.__code__))[1][1]
        insts: list[str] = []
        started = False
        for instr in dis.get_instructions(fn):
            if started and instr.starts_line:
                break
            pos = instr.positions
            if pos and pos.lineno == target_line:
                started = started or bool(instr.starts_line)
                insts.append(instr.opname)

        ops = insts[insts.index("END_FOR") + 1 :]
        idx = 0

        pre_store_ops = []
        while idx < len(ops) and ops[idx] != "STORE_FAST":
            pre_store_ops.append(ops[idx])
            idx += 1

        while idx < len(ops) and ops[idx] == "STORE_FAST":
            idx += 1

        return pre_store_ops, ops[idx] if idx < len(ops) else None