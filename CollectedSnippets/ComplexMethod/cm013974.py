def _cached_cleaned_instructions(
    code: types.CodeType, safe: bool = False
) -> Sequence[Instruction]:
    instructions = list(map(convert_instruction, dis.get_instructions(code)))
    # propagate now in case we remove some instructions
    propagate_line_nums(instructions)
    check_offsets(instructions)
    if sys.version_info >= (3, 11):
        populate_kw_names_argval(instructions, code.co_consts)
        virtualize_exception_table(code.co_exceptiontable, instructions)
    virtualize_jumps(instructions)
    strip_extended_args(instructions)
    if not safe:
        if sys.version_info < (3, 11):
            remove_load_call_method(instructions)
        if sys.version_info < (3, 12):
            explicit_super(code, instructions)
        if sys.version_info >= (3, 11):
            remove_jump_if_none(instructions)
            if sys.version_info >= (3, 12):
                remove_binary_store_slice(instructions)
            if sys.version_info >= (3, 13):
                remove_fused_load_store(instructions)
        if config.debug_force_graph_break_on_leaf_return:
            add_graph_break_if_leaf_instructions(instructions)
    if sys.version_info >= (3, 11):
        update_offsets(instructions)
        devirtualize_jumps(instructions)
    return instructions