def from_list(properties: list["Properties"]) -> "Properties":
        escaping_calls: dict[SimpleStmt, EscapingCall] = {}
        for p in properties:
            escaping_calls.update(p.escaping_calls)
        return Properties(
            escaping_calls=escaping_calls,
            escapes = any(p.escapes for p in properties),
            error_with_pop=any(p.error_with_pop for p in properties),
            error_without_pop=any(p.error_without_pop for p in properties),
            deopts=any(p.deopts for p in properties),
            deopts_periodic=any(p.deopts_periodic for p in properties),
            oparg=any(p.oparg for p in properties),
            jumps=any(p.jumps for p in properties),
            eval_breaker=any(p.eval_breaker for p in properties),
            needs_this=any(p.needs_this for p in properties),
            always_exits=any(p.always_exits for p in properties),
            sync_sp=any(p.sync_sp for p in properties),
            uses_co_consts=any(p.uses_co_consts for p in properties),
            uses_co_names=any(p.uses_co_names for p in properties),
            uses_locals=any(p.uses_locals for p in properties),
            uses_opcode=any(p.uses_opcode for p in properties),
            has_free=any(p.has_free for p in properties),
            side_exit=any(p.side_exit for p in properties),
            side_exit_at_end=any(p.side_exit_at_end for p in properties),
            pure=all(p.pure for p in properties),
            needs_prev=any(p.needs_prev for p in properties),
            no_save_ip=all(p.no_save_ip for p in properties),
            needs_guard_ip=any(p.needs_guard_ip for p in properties),
            unpredictable_jump=any(p.unpredictable_jump for p in properties),
            records_value=any(p.records_value for p in properties),
        )