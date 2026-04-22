def test_get_command_telemetry(self):
        """Test getting command telemetry via _get_command_telemetry."""
        # Test with dataframe command:
        command_metadata = metrics_util._get_command_telemetry(
            st.dataframe, "dataframe", pd.DataFrame(), width=250
        )

        self.assertEqual(command_metadata.name, "dataframe")
        self.assertEqual(len(command_metadata.args), 2)
        self.assertEqual(
            str(command_metadata.args[0]).strip(),
            'k: "data"\nt: "DataFrame"\nm: "len:0"',
        )
        self.assertEqual(
            str(command_metadata.args[1]).strip(),
            'k: "width"\nt: "int"',
        )

        # Test with text_input command:
        command_metadata = metrics_util._get_command_telemetry(
            st.text_input, "text_input", label="text input", value="foo", disabled=True
        )

        self.assertEqual(command_metadata.name, "text_input")
        self.assertEqual(len(command_metadata.args), 3)
        self.assertEqual(
            str(command_metadata.args[0]).strip(),
            'k: "label"\nt: "str"\nm: "len:10"',
        )
        self.assertEqual(
            str(command_metadata.args[1]).strip(),
            'k: "value"\nt: "str"\nm: "len:3"',
        )
        self.assertEqual(
            str(command_metadata.args[2]).strip(),
            'k: "disabled"\nt: "bool"\nm: "val:True"',
        )