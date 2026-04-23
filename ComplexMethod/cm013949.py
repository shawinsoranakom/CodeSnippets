def update_automatic_dynamic(
    tx: InstructionTranslator,
    name: str,
    entry: FrameStateSizeEntry,
    *,
    is_unspecialized_nn_module: bool = False,
) -> FrameStateSizeEntry:
    code_id = CodeId.make(tx.f_code, tx.closure)
    frame_state = get_code_state()[code_id]
    if torch._dynamo.config.automatic_dynamic_shapes:
        is_update = name in frame_state.automatic_dynamic
        mut_entry = frame_state.automatic_dynamic[name]
        old_entry = copy.copy(mut_entry)
        mut_entry |= entry

        # Do some logs (damn, I spend more code logging than I do actually doing
        # the updates lol)
        if is_update and old_entry.scalar != mut_entry.scalar:
            log.debug(
                "automatic dynamic int %s val %s != %s",
                name,
                entry.scalar,
                old_entry.scalar,
            )
            CompileEventLogger.instant(
                "automatic_dynamic",
                {
                    "name": name,
                    "dim_changed": "scalar",
                    "reason": "scalar change",
                    "cached": str(old_entry.scalar),
                    "new": str(entry.scalar),
                },
            )
            if is_unspecialized_nn_module:
                log.info(
                    "%s is converted to a symbolic integer. It is an attribute of a "
                    "user defined nn module class. If you wish to keep it static, you can "
                    "mark the nn module class as `torch._dynamo.mark_static`.",
                    name,
                )

        def log_tup(
            tup_name: str, short_reason: str, long_reason: str, i: int | None = None
        ) -> None:
            entry_tup = (
                getattr(entry, tup_name) if i is None else getattr(entry, tup_name)[i]
            )
            old_entry_tup = (
                getattr(old_entry, tup_name)
                if i is None
                else getattr(old_entry, tup_name)[i]
            )
            log.debug(
                "automatic dynamic %s %s %s %s != %s",
                tup_name,
                name,
                short_reason,
                # NB: We used to only report len(...) here for dim mismatch
                entry_tup,
                old_entry_tup,
            )
            CompileEventLogger.instant(
                "automatic_dynamic",
                {
                    "name": name,
                    "dim_changed": "all" if i is None else i,
                    "reason": long_reason,
                    "cached": str(old_entry_tup),
                    "new": str(entry_tup),
                },
            )

        if is_update and old_entry.size != mut_entry.size:
            if isinstance(old_entry.size, tuple) and isinstance(entry.size, tuple):
                if len(old_entry.size) != len(entry.size):
                    log_tup("size", "dim", "dimensionality change")
                else:
                    for i in range(len(entry.size)):
                        if old_entry.size[i] != entry.size[i]:
                            log_tup("size", f"size({i})", "size change", i)
            else:
                log_tup("size", "other", "other")

        if is_update and old_entry.stride != mut_entry.stride:
            if isinstance(old_entry.stride, tuple) and isinstance(entry.stride, tuple):
                if len(old_entry.stride) != len(entry.stride):
                    log_tup("stride", "dim", "dimensionality change")
                else:
                    for i in range(len(entry.stride)):
                        if old_entry.stride[i] != entry.stride[i]:
                            log_tup("stride", f"stride({i})", "stride change", i)
            else:
                log_tup("stride", "other", "other")
    else:
        old_entry = frame_state.automatic_dynamic[name]
        log.debug(
            "automatic dynamic is off, overwriting int %s val %s -> %s",
            name,
            old_entry.scalar,
            entry.scalar,
        )
        frame_state.automatic_dynamic[name] = entry
        mut_entry = entry

    return mut_entry