def remove_graph_break_if_leaf_instructions(instructions: list[Instruction]) -> None:
    new_insts = []
    for inst, next_inst in itertools.pairwise(instructions):
        if (
            inst.opname == "NOP"
            and inst.argval == "GRAPH_BREAK_IF_LEAF"
            and next_inst.opname.startswith("RETURN")
        ):
            # remove this instruction and update all other instructions' jump targets
            for i in range(len(instructions)):
                if instructions[i].target is inst:
                    instructions[i].target = next_inst
                if instructions[i].exn_tab_entry:
                    # linter is mistakenly complaining that None has no attribute "..."
                    # but this codepath only runs if instructions[i] is not None
                    if instructions[i].exn_tab_entry.start is inst:  # type: ignore[union-attr]
                        instructions[i].exn_tab_entry.start = next_inst  # type: ignore[union-attr]
                    if instructions[i].exn_tab_entry.end is inst:  # type: ignore[union-attr]
                        instructions[i].exn_tab_entry.end = next_inst  # type: ignore[union-attr]
                    if instructions[i].exn_tab_entry.target is inst:  # type: ignore[union-attr]
                        instructions[i].exn_tab_entry.target = next_inst  # type: ignore[union-attr]
        else:
            new_insts.append(inst)
    new_insts.append(instructions[-1])
    instructions[:] = new_insts