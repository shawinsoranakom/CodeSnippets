def test_file_edit_observation_get_edit_groups():
    """Test the get_edit_groups method."""
    obs = FileEditObservation(
        path='/test/file.txt',
        prev_exist=True,
        old_content='Line 1\nLine 2\nLine 3\nLine 4\n',
        new_content='Line 1\nNew Line 2\nLine 3\nNew Line 4\n',
        impl_source=FileEditSource.LLM_BASED_EDIT,
        content='Line 1\nLine 2\nLine 3\nLine 4\n',  # Initial content is old_content
    )

    groups = obs.get_edit_groups(n_context_lines=1)
    assert len(groups) > 0

    # Check structure of edit groups
    for group in groups:
        assert 'before_edits' in group
        assert 'after_edits' in group
        assert isinstance(group['before_edits'], list)
        assert isinstance(group['after_edits'], list)

    # Verify line numbers and content
    first_group = groups[0]
    assert any('Line 2' in line for line in first_group['before_edits'])
    assert any('New Line 2' in line for line in first_group['after_edits'])