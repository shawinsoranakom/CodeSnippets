def test_no_write_access(self):
        mo_file_en = Path(self.MO_FILE_EN)
        err_buffer = StringIO()
        # Put parent directory in read-only mode.
        old_mode = mo_file_en.parent.stat().st_mode
        mo_file_en.parent.chmod(stat.S_IRUSR | stat.S_IXUSR)
        # Ensure .po file is more recent than .mo file.
        mo_file_en.with_suffix(".po").touch()
        try:
            with self.assertRaisesMessage(
                CommandError, "compilemessages generated one or more errors."
            ):
                call_command(
                    "compilemessages", locale=["en"], stderr=err_buffer, verbosity=0
                )
            self.assertIn("not writable location", err_buffer.getvalue())
        finally:
            mo_file_en.parent.chmod(old_mode)