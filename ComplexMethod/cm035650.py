def test_file_read_action_legacy_serialization():
    original_action_dict = {
        'action': 'read',
        'args': {
            'path': '/workspace/test.txt',
            'start': 0,
            'end': -1,
            'thought': 'Reading the file contents',
            'impl_source': 'oh_aci',
            'translated_ipython_code': "print(file_editor(**{'command': 'view', 'path': '/workspace/test.txt'}))",
        },
    }

    event = event_from_dict(original_action_dict)
    assert isinstance(event, Action)
    assert isinstance(event, FileReadAction)

    # Common arguments
    assert event.path == '/workspace/test.txt'
    assert event.thought == 'Reading the file contents'
    assert event.impl_source == FileReadSource.OH_ACI
    assert not hasattr(event, 'translated_ipython_code')
    assert not hasattr(
        event, 'command'
    )  # FileReadAction should not have command attribute

    # Read-specific arguments
    assert event.start == 0
    assert event.end == -1

    event_dict = event_to_dict(event)
    assert 'translated_ipython_code' not in event_dict['args']
    assert (
        'command' not in event_dict['args']
    )  # command should not be in serialized args

    # Common arguments in serialized form
    assert event_dict['args']['path'] == '/workspace/test.txt'
    assert event_dict['args']['impl_source'] == 'oh_aci'
    assert event_dict['args']['thought'] == 'Reading the file contents'

    # Read-specific arguments in serialized form
    assert event_dict['args']['start'] == 0
    assert event_dict['args']['end'] == -1