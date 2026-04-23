def walk(state: ReadsWrites, start: int) -> None:
        if start in state.visited:
            return
        state.visited.add(start)

        for i in range(start, len(instructions)):
            inst = instructions[i]
            if inst.opcode in HASLOCAL or inst.opcode in HASFREE:
                if "LOAD" in inst.opname or "DELETE" in inst.opname:
                    if inst.argval not in must.writes:
                        state.reads.add(inst.argval)
                elif "STORE" in inst.opname:
                    state.writes.add(inst.argval)
                elif inst.opname == "MAKE_CELL":
                    pass
                else:
                    raise NotImplementedError(f"unhandled {inst.opname}")
            if inst.exn_tab_entry:
                walk(may, indexof[inst.exn_tab_entry.target])
            if inst.opcode in JUMP_OPCODES:
                assert inst.target is not None
                walk(may, indexof[inst.target])
                state = may
            if inst.opcode in TERMINAL_OPCODES:
                return