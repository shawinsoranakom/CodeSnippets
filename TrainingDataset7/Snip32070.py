def test_command_option(self):
        with self.assertLogs("test", "INFO") as cm:
            with captured_stdout():
                call_command(
                    "shell",
                    command=(
                        "import django; from logging import getLogger; "
                        'getLogger("test").info(django.__version__)'
                    ),
                )
        self.assertEqual(cm.records[0].getMessage(), __version__)