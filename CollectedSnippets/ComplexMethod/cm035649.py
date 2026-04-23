def test_file_ohaci_edit_action_legacy_serialization():
    original_action_dict = {
        'action': 'edit',
        'args': {
            'path': '/workspace/game_2048.py',
            'content': '',
            'start': 1,
            'end': -1,
            'thought': "I'll help you create a simple 2048 game in Python. I'll use the str_replace_editor to create the file.",
            'impl_source': 'oh_aci',
            'translated_ipython_code': "print(file_editor(**{'command': 'create', 'path': '/workspace/game_2048.py', 'file_text': 'New file content'}))",
        },
    }
    event = event_from_dict(original_action_dict)
    assert isinstance(event, Action)
    assert isinstance(event, FileEditAction)

    # Common arguments
    assert event.path == '/workspace/game_2048.py'
    assert (
        event.thought
        == "I'll help you create a simple 2048 game in Python. I'll use the str_replace_editor to create the file."
    )
    assert event.impl_source == FileEditSource.OH_ACI
    assert not hasattr(event, 'translated_ipython_code')

    # OH_ACI arguments
    assert event.command == 'create'
    assert event.file_text == 'New file content'
    assert event.old_str is None
    assert event.new_str is None
    assert event.insert_line is None

    # LLM-based editing arguments
    assert event.content == ''
    assert event.start == 1
    assert event.end == -1

    event_dict = event_to_dict(event)
    assert 'translated_ipython_code' not in event_dict['args']

    # Common arguments
    assert event_dict['args']['path'] == '/workspace/game_2048.py'
    assert event_dict['args']['impl_source'] == 'oh_aci'
    assert (
        event_dict['args']['thought']
        == "I'll help you create a simple 2048 game in Python. I'll use the str_replace_editor to create the file."
    )

    # OH_ACI arguments
    assert event_dict['args']['command'] == 'create'
    assert event_dict['args']['file_text'] == 'New file content'
    assert event_dict['args']['old_str'] is None
    assert event_dict['args']['new_str'] is None
    assert event_dict['args']['insert_line'] is None

    # LLM-based editing arguments
    assert event_dict['args']['content'] == ''
    assert event_dict['args']['start'] == 1
    assert event_dict['args']['end'] == -1