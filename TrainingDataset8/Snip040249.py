def test_run_arguments(self):
        """The correct command line should be passed downstream."""
        with patch("validators.url", return_value=False), patch(
            "os.path.exists", return_value=True
        ):
            with patch("streamlit.web.cli._main_run") as mock_main_run:
                result = self.runner.invoke(
                    cli,
                    [
                        "run",
                        "some script.py",
                        "argument with space",
                        "argument with another space",
                    ],
                )
        mock_main_run.assert_called_once()
        positional_args = mock_main_run.call_args[0]
        self.assertEqual(positional_args[0], "some script.py")
        self.assertEqual(
            positional_args[1],
            ("argument with space", "argument with another space"),
        )
        self.assertEqual(0, result.exit_code)