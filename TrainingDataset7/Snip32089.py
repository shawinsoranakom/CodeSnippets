def test_message_with_stdout_listing_objects_with_isort_not_installed(self):
        class TestCommand(shell.Command):
            def get_auto_imports(self):
                # Include duplicate import strings to ensure proper handling,
                # independent of isort's deduplication (#36252).
                return super().get_auto_imports() + [
                    "django.urls.reverse",
                    "django.urls.resolve",
                    "shell",
                    "django",
                    "django.urls.reverse",
                    "shell",
                    "django",
                ]

        with captured_stdout() as stdout:
            TestCommand().get_namespace(verbosity=2)

        self.assertEqual(
            stdout.getvalue().strip(),
            "13 objects imported automatically:\n\n"
            "  import shell\n"
            "  import django\n"
            "  from django.conf import settings\n"
            "  from django.db import connection, models, reset_queries\n"
            "  from django.db.models import functions\n"
            "  from django.utils import timezone\n"
            "  from django.contrib.contenttypes.models import ContentType\n"
            "  from shell.models import Phone, Marker\n"
            "  from django.urls import reverse, resolve",
        )