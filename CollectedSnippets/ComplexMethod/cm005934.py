def test_check_content_pattern(git_component, test_files):
    """Test content pattern matching."""
    temp_dir = Path(test_files)

    # Test simple content match
    assert git_component.check_content_pattern(temp_dir / "test.py", r"import langchain")
    assert not git_component.check_content_pattern(temp_dir / "test.txt", r"import langchain")

    # Test regex pattern
    assert git_component.check_content_pattern(temp_dir / "test.py", r"class.*Component")

    # Test binary file
    assert not git_component.check_content_pattern(temp_dir / "test.bin", r"Binary")

    # Test invalid regex patterns
    assert not git_component.check_content_pattern(temp_dir / "test.py", r"[")  # Unclosed bracket
    assert not git_component.check_content_pattern(temp_dir / "test.py", r"*")  # Invalid quantifier
    assert not git_component.check_content_pattern(temp_dir / "test.py", r"(?<)")  # Invalid lookbehind
    assert not git_component.check_content_pattern(temp_dir / "test.py", r"\1")