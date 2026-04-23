def _init_worker(
    counter,
    initial_settings=None,
    serialized_contents=None,
    process_setup=None,
    process_setup_args=None,
    debug_mode=None,
    used_aliases=None,
):
    """
    Switch to databases dedicated to this worker and run system checks.

    This helper lives at module-level because of the multiprocessing module's
    requirements.
    """

    global _worker_id

    with counter.get_lock():
        counter.value += 1
        _worker_id = counter.value

    is_spawn_or_forkserver = multiprocessing.get_start_method() in {
        "forkserver",
        "spawn",
    }

    if is_spawn_or_forkserver:
        if process_setup and callable(process_setup):
            if process_setup_args is None:
                process_setup_args = ()
            process_setup(*process_setup_args)
        django.setup()
        setup_test_environment(debug=debug_mode)

    db_aliases = used_aliases if used_aliases is not None else connections
    for alias in db_aliases:
        connection = connections[alias]
        if is_spawn_or_forkserver:
            # Restore initial settings in spawned processes.
            connection.settings_dict.update(initial_settings[alias])
            if value := serialized_contents.get(alias):
                connection._test_serialized_contents = value
        connection.creation.setup_worker_connection(_worker_id)
        if (
            is_spawn_or_forkserver
            and os.environ.get("RUNNING_DJANGOS_TEST_SUITE") == "true"
        ):
            connection.creation.mark_expected_failures_and_skips()

    if is_spawn_or_forkserver:
        call_command(
            "check", stdout=io.StringIO(), stderr=io.StringIO(), databases=used_aliases
        )