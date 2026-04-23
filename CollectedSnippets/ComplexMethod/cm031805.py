def compute_properties(op: parser.CodeDef) -> Properties:
    escaping_calls = find_escaping_api_calls(op)
    has_free = (
        variable_used(op, "PyCell_New")
        or variable_used(op, "PyCell_GetRef")
        or variable_used(op, "PyCell_SetTakeRef")
        or variable_used(op, "PyCell_SwapTakeRef")
    )
    deopts_if = variable_used(op, "DEOPT_IF")
    exits_if = variable_used(op, "EXIT_IF")
    exit_if_at_end = variable_used(op, "AT_END_EXIT_IF")
    deopts_periodic = variable_used(op, "HANDLE_PENDING_AND_DEOPT_IF")
    exits_and_deopts = sum((deopts_if, exits_if, deopts_periodic))
    if exits_and_deopts > 1:
        tkn = op.tokens[0]
        raise lexer.make_syntax_error(
            "Op cannot contain more than one of EXIT_IF, DEOPT_IF and HANDLE_PENDING_AND_DEOPT_IF",
            tkn.filename,
            tkn.line,
            tkn.column,
            op.name,
        )
    error_with_pop = has_error_with_pop(op)
    error_without_pop = has_error_without_pop(op)
    escapes = stmt_escapes(op.block)
    pure = False if isinstance(op, parser.LabelDef) else "pure" in op.annotations
    no_save_ip = False if isinstance(op, parser.LabelDef) else "no_save_ip" in op.annotations
    unpredictable, branches_seen = stmt_has_jump_on_unpredictable_path(op.block, 0)
    unpredictable_jump = False if isinstance(op, parser.LabelDef) else (unpredictable and branches_seen > 0)
    return Properties(
        escaping_calls=escaping_calls,
        escapes=escapes,
        error_with_pop=error_with_pop,
        error_without_pop=error_without_pop,
        deopts=deopts_if,
        deopts_periodic=deopts_periodic,
        side_exit=exits_if,
        side_exit_at_end=exit_if_at_end,
        oparg=oparg_used(op),
        jumps=variable_used(op, "JUMPBY"),
        eval_breaker="CHECK_PERIODIC" in op.name,
        needs_this=variable_used(op, "this_instr"),
        always_exits=always_exits(op),
        sync_sp=variable_used(op, "SYNC_SP"),
        uses_co_consts=variable_used(op, "FRAME_CO_CONSTS"),
        uses_co_names=variable_used(op, "FRAME_CO_NAMES"),
        uses_locals=variable_used(op, "GETLOCAL") and not has_free,
        uses_opcode=variable_used(op, "opcode"),
        has_free=has_free,
        pure=pure,
        no_save_ip=no_save_ip,
        tier=tier_variable(op),
        needs_prev=variable_used(op, "prev_instr"),
        needs_guard_ip=(isinstance(op, parser.InstDef)
                        and (unpredictable_jump and "replaced" not in op.annotations))
                       or variable_used(op, "LOAD_IP")
                       or variable_used(op, "DISPATCH_INLINED"),
        unpredictable_jump=unpredictable_jump,
        records_value=variable_used(op, "RECORD_VALUE")
    )