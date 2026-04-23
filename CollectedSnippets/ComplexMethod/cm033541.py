def test_play_context(mocker, parser, reset_cli_args):
    options = parser.parse_args(['-vv', '--check'])
    context._init_global_context(options)
    play = Play.load({})
    play_context = PlayContext(play=play)

    assert play_context.remote_addr is None
    assert play_context.remote_user is None
    assert play_context.password == ''
    assert play_context.private_key_file == C.DEFAULT_PRIVATE_KEY_FILE
    assert play_context.timeout == C.DEFAULT_TIMEOUT
    assert getattr(play_context, 'verbosity', None) is None
    assert play_context.check_mode is True

    mock_play = mocker.MagicMock()
    mock_play.force_handlers = True

    play_context = PlayContext(play=mock_play)
    assert play_context.force_handlers is True

    mock_task = mocker.MagicMock()
    mock_task.connection = 'mocktask'
    mock_task.remote_user = 'mocktask'
    mock_task.port = 1234
    mock_task.no_log = True
    mock_task.become = True
    mock_task.become_method = 'mocktask'
    mock_task.become_user = 'mocktaskroot'
    mock_task.become_pass = 'mocktaskpass'
    mock_task._local_action = False
    mock_task.delegate_to = None

    all_vars = dict(
        ansible_connection='mock_inventory',
        ansible_ssh_port=4321,
    )

    mock_templar = mocker.MagicMock()

    play_context = PlayContext()
    play_context = play_context.set_task_and_variable_override(task=mock_task, variables=all_vars, templar=mock_templar)

    assert play_context.connection == 'mock_inventory'
    assert play_context.remote_user == 'mocktask'
    assert play_context.no_log is True

    mock_task.no_log = False
    play_context = play_context.set_task_and_variable_override(task=mock_task, variables=all_vars, templar=mock_templar)
    assert play_context.no_log is False