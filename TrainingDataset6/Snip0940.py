def test_on_first_run(usage_tracker_io, usage_tracker_exists, shell_pid, logs):
    shell_pid.return_value = 12
    main()
    usage_tracker_exists.return_value = False
    _assert_tracker_updated(usage_tracker_io, 12)
    logs.how_to_configure_alias.assert_called_once()