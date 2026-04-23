def test_file_edit_observation_legacy_serialization():
    original_observation_dict = {
        'observation': 'edit',
        'content': 'content',
        'extras': {
            'path': '/workspace/game_2048.py',
            'prev_exist': False,
            'old_content': None,
            'new_content': 'new content',
            'impl_source': 'oh_aci',
            'formatted_output_and_error': 'File created successfully at: /workspace/game_2048.py',
        },
    }

    event = event_from_dict(original_observation_dict)
    assert isinstance(event, Observation)
    assert isinstance(event, FileEditObservation)
    assert event.impl_source == FileEditSource.OH_ACI
    assert event.path == '/workspace/game_2048.py'
    assert event.prev_exist is False
    assert event.old_content is None
    assert event.new_content == 'new content'
    assert not hasattr(event, 'formatted_output_and_error')

    event_dict = event_to_dict(event)
    assert event_dict['extras']['impl_source'] == 'oh_aci'
    assert event_dict['extras']['path'] == '/workspace/game_2048.py'
    assert event_dict['extras']['prev_exist'] is False
    assert event_dict['extras']['old_content'] is None
    assert event_dict['extras']['new_content'] == 'new content'
    assert 'formatted_output_and_error' not in event_dict['extras']