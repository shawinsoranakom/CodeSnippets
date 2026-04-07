def test_message_with_stdout_listing_objects_with_isort(self):
        sorted_imports = (
            "  from shell.models import Marker, Phone\n\n"
            "  from django.db import connection, models, reset_queries\n"
            "  from django.db.models import functions\n"
            "  from django.contrib.contenttypes.models import ContentType\n"
            "  from django.conf import settings\n"
            "  from django.utils import timezone"
        )
        mock_isort_code = mock.Mock(code=mock.MagicMock(return_value=sorted_imports))

        class TestCommand(shell.Command):
            def get_auto_imports(self):
                return super().get_auto_imports() + [
                    "django.urls.reverse",
                    "django.urls.resolve",
                    "django",
                ]

        with (
            mock.patch.dict(sys.modules, {"isort": mock_isort_code}),
            captured_stdout() as stdout,
        ):
            TestCommand().get_namespace(verbosity=2)

        self.assertEqual(
            stdout.getvalue().strip(),
            "12 objects imported automatically:\n\n" + sorted_imports,
        )