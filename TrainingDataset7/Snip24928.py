def test_bom_rejection(self):
        stderr = StringIO()
        with self.assertRaisesMessage(
            CommandError, "compilemessages generated one or more errors."
        ):
            call_command(
                "compilemessages", locale=[self.LOCALE], verbosity=0, stderr=stderr
            )
        self.assertIn("file has a BOM (Byte Order Mark)", stderr.getvalue())
        self.assertFalse(os.path.exists(self.MO_FILE))