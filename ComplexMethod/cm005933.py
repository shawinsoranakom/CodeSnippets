def test_check_file_patterns(git_component, test_files):
    """Test file pattern matching."""
    temp_dir = Path(test_files)

    # Test single pattern
    assert git_component.check_file_patterns(temp_dir / "test.py", "*.py")
    assert not git_component.check_file_patterns(temp_dir / "test.txt", "*.py")

    # Test exclusion pattern
    assert not git_component.check_file_patterns(temp_dir / "test.py", "!*.py")

    # Test multiple patterns
    assert git_component.check_file_patterns(temp_dir / "test.py", "*.py,*.txt")
    assert git_component.check_file_patterns(temp_dir / "test.txt", "*.py,*.txt")

    # Test mixed include/exclude
    assert not git_component.check_file_patterns(temp_dir / "test.py", "*.py,!test.py")
    assert git_component.check_file_patterns(temp_dir / "other.py", "*.py,!test.py")

    # Test empty pattern (should include all)
    assert git_component.check_file_patterns(temp_dir / "test.py", "")
    assert git_component.check_file_patterns(temp_dir / "test.txt", "  ")

    # Test invalid pattern (should treat as literal string)
    assert not git_component.check_file_patterns(temp_dir / "test.py", "[")