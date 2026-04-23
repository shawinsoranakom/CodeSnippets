def test_reboot_command(action_plugin, mocker, monkeypatch, task_args):
    """Check that the reboot command gets called and reboot verified."""
    def _patched_low_level_execute_command(cmd, *args, **kwargs):
        return {
            _SENTINEL_TEST_COMMAND: {
                'rc': 0,
                'stderr': '<test command stub-stderr>',
                'stdout': '<test command stub-stdout>',
            },
            _SENTINEL_REBOOT_COMMAND: {
                'rc': 0,
                'stderr': '<reboot command stub-stderr>',
                'stdout': '<reboot command stub-stdout>',
            },
            f'{_SENTINEL_SHORT_REBOOT_COMMAND} ': {  # no args is concatenated
                'rc': 0,
                'stderr': '<short reboot command stub-stderr>',
                'stdout': '<short reboot command stub-stdout>',
            },
        }[cmd]

    monkeypatch.setattr(
        action_plugin,
        '_low_level_execute_command',
        _patched_low_level_execute_command,
    )

    action_plugin._connection = mocker.Mock()

    monkeypatch.setattr(action_plugin, 'check_boot_time', lambda *_a, **_kw: 5)
    monkeypatch.setattr(action_plugin, 'get_distribution', mocker.MagicMock())
    monkeypatch.setattr(action_plugin, 'get_system_boot_time', lambda d: 0)

    low_level_cmd_spy = mocker.spy(action_plugin, '_low_level_execute_command')

    action_result = action_plugin.run()

    assert low_level_cmd_spy.called

    expected_reboot_command = (
        task_args['reboot_command'] if ' ' in task_args['reboot_command']
        else f'{task_args["reboot_command"] !s} '
    )
    low_level_cmd_spy.assert_any_call(expected_reboot_command, sudoable=True)
    low_level_cmd_spy.assert_any_call(task_args['test_command'], sudoable=True)

    assert low_level_cmd_spy.call_count == 2
    assert low_level_cmd_spy.spy_return == {
        'rc': 0,
        'stderr': '<test command stub-stderr>',
        'stdout': '<test command stub-stdout>',
    }
    assert low_level_cmd_spy.spy_exception is None

    assert 'failed' not in action_result
    assert action_result == {'rebooted': True, 'changed': True, 'elapsed': 0}