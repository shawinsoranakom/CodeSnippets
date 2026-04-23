def test_combined_filter(git_component, test_files):
    """Test the combined filter function."""
    temp_dir = Path(test_files)

    # Test with both patterns
    filter_func = git_component.build_combined_filter(
        file_filter_patterns="*.py", content_filter_pattern=r"class.*Component"
    )
    assert filter_func(str(temp_dir / "test.py"))
    assert not filter_func(str(temp_dir / "test.txt"))
    assert not filter_func(str(temp_dir / "test.bin"))

    # Test with only file pattern
    filter_func = git_component.build_combined_filter(file_filter_patterns="*.py")
    assert filter_func(str(temp_dir / "test.py"))
    assert not filter_func(str(temp_dir / "test.txt"))

    # Test with only content pattern
    filter_func = git_component.build_combined_filter(content_filter_pattern=r"class.*Component")
    assert filter_func(str(temp_dir / "test.py"))
    assert not filter_func(str(temp_dir / "test.txt"))

    # Test with empty patterns
    filter_func = git_component.build_combined_filter()
    assert filter_func(str(temp_dir / "test.py"))
    assert filter_func(str(temp_dir / "test.txt"))
    assert not filter_func(str(temp_dir / "test.bin"))  # Binary files still excluded

    # Test error cases
    filter_func = git_component.build_combined_filter(
        file_filter_patterns="*.py", content_filter_pattern=r"class.*Component"
    )
    assert not filter_func(str(temp_dir / "nonexistent.txt"))  # Non-existent file
    assert not filter_func(str(temp_dir / "no_access" / "secret.txt"))