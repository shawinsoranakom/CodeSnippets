def test_build_ignore_patterns(collection_input, monkeypatch):
    input_dir = collection_input[0]

    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'vvv', mock_display)

    actual = collection._build_files_manifest(to_bytes(input_dir), 'namespace', 'collection',
                                              ['*.md', 'plugins/action', 'playbooks/*.j2'],
                                              Sentinel, None)
    assert actual['format'] == 1

    expected_missing = [
        'README.md',
        'docs/My Collection.md',
        'plugins/action',
        'playbooks/templates/test.conf.j2',
        'playbooks/templates/subfolder/test.conf.j2',
    ]

    # Files or dirs that are close to a match but are not, make sure they are present
    expected_present = [
        'docs',
        'roles/common/templates/test.conf.j2',
        'roles/common/templates/subfolder/test.conf.j2',
    ]

    actual_files = [e['name'] for e in actual['files']]
    for m in expected_missing:
        assert m not in actual_files

    for p in expected_present:
        assert p in actual_files

    expected_msgs = [
        "Skipping '%s/galaxy.yml' for collection build" % to_text(input_dir),
        "Skipping '%s/README.md' for collection build" % to_text(input_dir),
        "Skipping '%s/docs/My Collection.md' for collection build" % to_text(input_dir),
        "Skipping '%s/plugins/action' for collection build" % to_text(input_dir),
        "Skipping '%s/playbooks/templates/test.conf.j2' for collection build" % to_text(input_dir),
        "Skipping '%s/playbooks/templates/subfolder/test.conf.j2' for collection build" % to_text(input_dir),
    ]
    assert mock_display.call_count == len(expected_msgs)
    assert mock_display.mock_calls[0][1][0] in expected_msgs
    assert mock_display.mock_calls[1][1][0] in expected_msgs
    assert mock_display.mock_calls[2][1][0] in expected_msgs
    assert mock_display.mock_calls[3][1][0] in expected_msgs
    assert mock_display.mock_calls[4][1][0] in expected_msgs
    assert mock_display.mock_calls[5][1][0] in expected_msgs