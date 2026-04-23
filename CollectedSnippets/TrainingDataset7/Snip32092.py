def test_message_with_stdout_no_installed_apps(self):
        cases = {
            0: "",
            1: "6 objects imported automatically (use -v 2 for details).",
            2: "6 objects imported automatically:\n\n"
            "  from django.conf import settings\n"
            "  from django.db import connection, models, reset_queries\n"
            "  from django.db.models import functions\n"
            "  from django.utils import timezone",
        }
        for verbosity, expected in cases.items():
            with self.subTest(verbosity=verbosity):
                with captured_stdout() as stdout:
                    shell.Command().get_namespace(verbosity=verbosity)
                    self.assertEqual(stdout.getvalue().strip(), expected)