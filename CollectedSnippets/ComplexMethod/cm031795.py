def cflags(p: Properties) -> str:
    flags: list[str] = []
    if p.oparg:
        flags.append("HAS_ARG_FLAG")
    if p.uses_co_consts:
        flags.append("HAS_CONST_FLAG")
    if p.uses_co_names:
        flags.append("HAS_NAME_FLAG")
    if p.jumps:
        flags.append("HAS_JUMP_FLAG")
    if p.has_free:
        flags.append("HAS_FREE_FLAG")
    if p.uses_locals:
        flags.append("HAS_LOCAL_FLAG")
    if p.eval_breaker:
        flags.append("HAS_EVAL_BREAK_FLAG")
    if p.deopts:
        flags.append("HAS_DEOPT_FLAG")
    if p.deopts_periodic:
        flags.append("HAS_PERIODIC_FLAG")
    if p.side_exit or p.side_exit_at_end:
        flags.append("HAS_EXIT_FLAG")
    if not p.infallible:
        flags.append("HAS_ERROR_FLAG")
    if p.error_without_pop:
        flags.append("HAS_ERROR_NO_POP_FLAG")
    if p.escapes:
        flags.append("HAS_ESCAPES_FLAG")
    if p.pure:
        flags.append("HAS_PURE_FLAG")
    if p.no_save_ip:
        flags.append("HAS_NO_SAVE_IP_FLAG")
    if p.sync_sp:
        flags.append("HAS_SYNC_SP_FLAG")
    if p.unpredictable_jump:
        flags.append("HAS_UNPREDICTABLE_JUMP_FLAG")
    if p.needs_guard_ip:
        flags.append("HAS_NEEDS_GUARD_IP_FLAG")
    if p.records_value:
        flags.append("HAS_RECORDS_VALUE_FLAG")
    if flags:
        return " | ".join(flags)
    else:
        return "0"