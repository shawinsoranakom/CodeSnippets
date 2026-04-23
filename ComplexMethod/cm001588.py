def apply_and_restart(disable_list, update_list, disable_all):
    check_access()

    disabled = json.loads(disable_list)
    assert type(disabled) == list, f"wrong disable_list data for apply_and_restart: {disable_list}"

    update = json.loads(update_list)
    assert type(update) == list, f"wrong update_list data for apply_and_restart: {update_list}"

    if update:
        save_config_state("Backup (pre-update)")

    update = set(update)

    for ext in extensions.extensions:
        if ext.name not in update:
            continue

        try:
            ext.fetch_and_reset_hard()
        except Exception:
            errors.report(f"Error getting updates for {ext.name}", exc_info=True)

    shared.opts.disabled_extensions = disabled
    shared.opts.disable_all_extensions = disable_all
    shared.opts.save(shared.config_filename)

    if restart.is_restartable():
        restart.restart_program()
    else:
        restart.stop_program()