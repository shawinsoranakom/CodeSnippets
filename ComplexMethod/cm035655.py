def test_legacy_serialization():
    original_observation_dict = {
        'id': 42,
        'source': 'agent',
        'timestamp': '2021-08-01T12:00:00',
        'observation': 'run',
        'message': 'Command `ls -l` executed with exit code 0.',
        'extras': {
            'command': 'ls -l',
            'hidden': False,
            'exit_code': 0,
            'command_id': 3,
        },
        'content': 'foo.txt',
        'success': True,
    }
    event = event_from_dict(original_observation_dict)
    assert isinstance(event, Observation)
    assert isinstance(event, CmdOutputObservation)
    assert event.metadata.exit_code == 0
    assert event.success is True
    assert event.command == 'ls -l'
    assert event.hidden is False

    event_dict = event_to_dict(event)
    assert event_dict['success'] is True
    assert event_dict['extras']['metadata']['exit_code'] == 0
    assert event_dict['extras']['metadata']['pid'] == 3
    assert event_dict['extras']['command'] == 'ls -l'
    assert event_dict['extras']['hidden'] is False