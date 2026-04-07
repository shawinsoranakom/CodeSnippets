def test_validate_after_internal_save(self):
        s = CustomStorage()
        # The initial name passed to `save` is valid and safe, but the result
        # from `_save` is not (this is achieved by monkeypatching _save).
        for name in self.invalid_file_names:
            with (
                self.subTest(name=name),
                mock.patch.object(s, "_save", return_value=name),
            ):

                with self.assertRaisesMessage(
                    SuspiciousFileOperation, self.error_msg % name
                ):
                    s.save("valid-file-name.txt", content="irrelevant")