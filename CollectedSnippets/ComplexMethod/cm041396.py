def test_parse_config_file(input_type, sections):
    config_string = CONFIG_FILE_SECTION.lstrip()

    # generate config string
    if sections == 0:
        config_string = config_string.partition("\n")[2]
    config_string = "\n".join(
        [config_string.replace("{section}", str(i)) for i in range(max(sections, 1))]
    )

    # parse result
    config_input = config_string
    if input_type == "file":
        config_input = new_tmp_file()  # deleted on shutdown
        save_file(config_input, config_string)
    result = parse_config_file(config_input)

    # run assertions
    expected = {
        "var1": "foo bar 123",
        "var2": "123.45",
        "var3": "Test string' <with% special { chars!",
    }
    if sections <= 1:
        assert expected == result
    else:
        assert sections == len(result)
        for section in result.values():
            assert expected == section