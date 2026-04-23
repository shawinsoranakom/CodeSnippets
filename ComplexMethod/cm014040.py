def _bytecode_from_template_with_split(
    template: Callable[..., Any],
    stack_index: int,
    varname_map: dict[str, Any] | None = None,
) -> tuple[list[Instruction], list[Instruction]]:
    template_code = bytecode_from_template(template, varname_map=varname_map)
    template_code.append(create_instruction("POP_TOP"))

    # adjust exception table entry depth
    for inst in template_code:
        if inst.exn_tab_entry:
            inst.exn_tab_entry.depth += stack_index

    # search for LOAD_FAST dummy and replace it with 2 NOPs (we can break up the bytecode between them)
    dummy_idx, dummy_inst = next(
        (
            (i, inst)
            for i, inst in enumerate(template_code)
            if inst.opname in ("LOAD_FAST", "LOAD_FAST_BORROW")
            and inst.argval == "dummy"
        ),
        (None, None),
    )
    assert dummy_idx is not None and dummy_inst is not None

    # replace LOAD_FAST dummy with first NOP marking exception area
    overwrite_instruction(dummy_inst, [create_instruction("NOP")])

    # POP_TOP follows LOAD_FAST dummy - replace with NOP marking end of exception area
    assert template_code[dummy_idx + 1].opname == "POP_TOP"
    overwrite_instruction(template_code[dummy_idx + 1], [create_instruction("NOP")])

    return template_code[: dummy_idx + 1], template_code[dummy_idx + 1 :]