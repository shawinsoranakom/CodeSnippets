def test_cmd_run_action_legacy_serialization():
    original_action_dict = {
        'action': 'run',
        'args': {
            'blocking': False,
            'command': 'echo "Hello world"',
            'thought': '',
            'hidden': False,
            'confirmation_state': ActionConfirmationStatus.CONFIRMED,
            'keep_prompt': False,  # will be treated as no-op
        },
    }
    event = event_from_dict(original_action_dict)
    assert isinstance(event, Action)
    assert isinstance(event, CmdRunAction)
    assert event.command == 'echo "Hello world"'
    assert event.hidden is False
    assert not hasattr(event, 'keep_prompt')

    event_dict = event_to_dict(event)
    assert 'keep_prompt' not in event_dict['args']
    assert (
        event_dict['args']['confirmation_state'] == ActionConfirmationStatus.CONFIRMED
    )
    assert event_dict['args']['blocking'] is False
    assert event_dict['args']['command'] == 'echo "Hello world"'
    assert event_dict['args']['thought'] == ''
    assert event_dict['args']['is_input'] is False