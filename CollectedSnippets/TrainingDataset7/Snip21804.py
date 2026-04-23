def test_validate_after_get_available_name(self):
        s = CustomStorage()
        # The initial name passed to `save` is valid and safe, but the returned
        # name from `get_available_name` is not.
        for name in self.invalid_file_names:
            with (
                self.subTest(name=name),
                mock.patch.object(s, "get_available_name", return_value=name),
                mock.patch.object(s, "_save") as mock_internal_save,
            ):
                with self.assertRaisesMessage(
                    SuspiciousFileOperation, self.error_msg % name
                ):
                    s.save("valid-file-name.txt", content="irrelevant")
                self.assertEqual(mock_internal_save.mock_calls, [])