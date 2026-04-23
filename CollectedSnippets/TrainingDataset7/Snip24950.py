def test_msgfmt_error_including_non_ascii(self):
        # po file contains invalid msgstr content (triggers non-ascii error
        # content). Make sure the output of msgfmt is unaffected by the current
        # locale.
        env = os.environ.copy()
        env.update({"LC_ALL": "C"})
        with mock.patch(
            "django.core.management.utils.run",
            lambda *args, **kwargs: run(*args, env=env, **kwargs),
        ):
            stderr = StringIO()
            with self.assertRaisesMessage(
                CommandError, "compilemessages generated one or more errors"
            ):
                call_command(
                    "compilemessages", locale=["ko"], stdout=StringIO(), stderr=stderr
                )
            if self.msgfmt_version < (0, 25):
                error_msg = "' cannot start a field name"
            else:
                error_msg = (
                    "a field name starts with a character that is not alphanumerical "
                    "or underscore"
                )
            self.assertIn(error_msg, stderr.getvalue())