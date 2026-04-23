def test_default_config_options_commented_out(self, patched_echo):
        config_options = create_config_options(
            {
                "server.address": "example.com",  # overrides default
                "server.port": 8501,  # explicitly set to default
            }
        )

        config_util.show_config(CONFIG_SECTION_DESCRIPTIONS, config_options)

        [(args, _)] = patched_echo.call_args_list
        # Remove the ascii escape sequences used to color terminal output.
        output = re.compile(r"\x1b[^m]*m").sub("", args[0])
        lines = set(output.split("\n"))

        # Config options not explicitly set should be commented out.
        assert "# runOnSave = false" in lines

        # Config options explicitly set should *not* be commented out, even if
        # they are set to their default values.
        assert 'address = "example.com"' in lines
        assert "port = 8501" in lines