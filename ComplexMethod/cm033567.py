def test_yaml_parser_error(
        content: t.Any,
        expected_message: str,
        expect_help_text: bool,
        line: int | None,
        col: int | None,
        mocker: pytest_mock.MockerFixture,
) -> None:
    set_duplicate_yaml_dict_key_config(mocker, 'error')

    expected_message = f'YAML parsing failed: {expected_message}'

    with tempfile.TemporaryDirectory() as tempdir:
        source_path = pathlib.Path(tempdir) / 'source.yml'
        source_path.write_text(str(content))

        with pytest.raises(AnsibleYAMLParserError) as error:
            from_yaml(content, file_name=str(source_path))

    assert error.value.message == expected_message
    assert error.value._original_message == expected_message
    assert format_exception_message(error.value) == expected_message
    assert str(error.value) == expected_message

    assert error.value.obj == Origin(path=str(source_path), line_num=line, col_num=col)

    if expect_help_text:
        assert error.value._help_text is not None  # DTFIX-FUTURE: check the content later once it's less volatile
    else:
        assert error.value._help_text is None