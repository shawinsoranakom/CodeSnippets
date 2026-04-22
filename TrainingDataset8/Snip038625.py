def test_ui_section_hidden(self, patched_echo):
        config_options = create_config_options({})

        config_util.show_config(CONFIG_SECTION_DESCRIPTIONS, config_options)

        [(args, _)] = patched_echo.call_args_list
        # Remove the ascii escape sequences used to color terminal output.
        output = re.compile(r"\x1b[^m]*m").sub("", args[0])
        lines = set(output.split("\n"))

        assert "[ui]" not in lines
        assert "# hideTopBar = false" not in lines