def test_to_snake_case():
    """Test _to_snake_case static method."""
    assert PoliciesComponent._to_snake_case("My Project") == "my_project"
    assert PoliciesComponent._to_snake_case("Test-Project") == "test_project"
    assert PoliciesComponent._to_snake_case("User's Project") == "user_s_project"
    assert PoliciesComponent._to_snake_case("Project, Name") == "project_name"
    assert PoliciesComponent._to_snake_case("UPPERCASE") == "uppercase"
    assert PoliciesComponent._to_snake_case("Mixed-Case Project's Name") == "mixed_case_project_s_name"

    # Test path traversal prevention
    assert PoliciesComponent._to_snake_case("../../etc/passwd") == "etc_passwd"
    assert PoliciesComponent._to_snake_case("../../../root") == "root"
    assert PoliciesComponent._to_snake_case("./hidden") == "hidden"
    assert PoliciesComponent._to_snake_case("path/to/file") == "path_to_file"
    assert PoliciesComponent._to_snake_case("back\\slash\\path") == "back_slash_path"

    # Test special characters are sanitized
    assert PoliciesComponent._to_snake_case("test@#$%project") == "test_project"
    assert PoliciesComponent._to_snake_case("___multiple___underscores___") == "multiple_underscores"

    # Test empty/invalid input
    with pytest.raises(ValueError, match="must contain at least one alphanumeric character"):
        PoliciesComponent._to_snake_case("...")
    with pytest.raises(ValueError, match="must contain at least one alphanumeric character"):
        PoliciesComponent._to_snake_case("___")
    with pytest.raises(ValueError, match="must contain at least one alphanumeric character"):
        PoliciesComponent._to_snake_case("@#$%")