def test_hello_command(self):
        """Tests the hello command runs the hello script in streamlit"""
        from streamlit.hello import Hello

        with patch("streamlit.web.cli._main_run") as mock_main_run:
            self.runner.invoke(cli, ["hello"])

            mock_main_run.assert_called_once()
            positional_args = mock_main_run.call_args[0]
            self.assertEqual(positional_args[0], Hello.__file__)