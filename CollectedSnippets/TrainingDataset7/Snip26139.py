def test_backend_arg(self):
        """Test backend argument of mail.get_connection()"""
        self.assertIsInstance(
            mail.get_connection("django.core.mail.backends.smtp.EmailBackend"),
            smtp.EmailBackend,
        )
        self.assertIsInstance(
            mail.get_connection("django.core.mail.backends.locmem.EmailBackend"),
            locmem.EmailBackend,
        )
        self.assertIsInstance(
            mail.get_connection("django.core.mail.backends.dummy.EmailBackend"),
            dummy.EmailBackend,
        )
        self.assertIsInstance(
            mail.get_connection("django.core.mail.backends.console.EmailBackend"),
            console.EmailBackend,
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            self.assertIsInstance(
                mail.get_connection(
                    "django.core.mail.backends.filebased.EmailBackend",
                    file_path=tmp_dir,
                ),
                filebased.EmailBackend,
            )

        msg = " not object"
        with self.assertRaisesMessage(TypeError, msg):
            mail.get_connection(
                "django.core.mail.backends.filebased.EmailBackend", file_path=object()
            )
        self.assertIsInstance(mail.get_connection(), locmem.EmailBackend)