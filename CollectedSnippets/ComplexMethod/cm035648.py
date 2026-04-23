def test_file_llm_based_edit_action_legacy_serialization():
    original_action_dict = {
        'action': 'edit',
        'args': {
            'path': '/path/to/file.txt',
            'content': 'dummy content',
            'start': 1,
            'end': -1,
            'thought': 'Replacing text',
            'impl_source': 'oh_aci',
            'translated_ipython_code': None,
        },
    }
    event = event_from_dict(original_action_dict)
    assert isinstance(event, Action)
    assert isinstance(event, FileEditAction)

    # Common arguments
    assert event.path == '/path/to/file.txt'
    assert event.thought == 'Replacing text'
    assert event.impl_source == FileEditSource.OH_ACI
    assert not hasattr(event, 'translated_ipython_code')

    # OH_ACI arguments
    assert event.command == ''
    assert event.file_text is None
    assert event.old_str is None
    assert event.new_str is None
    assert event.insert_line is None

    # LLM-based editing arguments
    assert event.content == 'dummy content'
    assert event.start == 1
    assert event.end == -1

    event_dict = event_to_dict(event)
    assert 'translated_ipython_code' not in event_dict['args']

    # Common arguments
    assert event_dict['args']['path'] == '/path/to/file.txt'
    assert event_dict['args']['impl_source'] == 'oh_aci'
    assert event_dict['args']['thought'] == 'Replacing text'

    # OH_ACI arguments
    assert event_dict['args']['command'] == ''
    assert event_dict['args']['file_text'] is None
    assert event_dict['args']['old_str'] is None
    assert event_dict['args']['new_str'] is None
    assert event_dict['args']['insert_line'] is None

    # LLM-based editing arguments
    assert event_dict['args']['content'] == 'dummy content'
    assert event_dict['args']['start'] == 1
    assert event_dict['args']['end'] == -1