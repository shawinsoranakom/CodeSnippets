def test_validate_before_get_available_name(self):
        s = CustomStorage()
        # The initial name passed to `save` is not valid nor safe, fail early.
        for name in self.invalid_file_names:
            with (
                self.subTest(name=name),
                mock.patch.object(s, "get_available_name") as mock_get_available_name,
                mock.patch.object(s, "_save") as mock_internal_save,
            ):
                with self.assertRaisesMessage(
                    SuspiciousFileOperation, self.error_msg % name
                ):
                    s.save(name, content="irrelevant")
                self.assertEqual(mock_get_available_name.mock_calls, [])
                self.assertEqual(mock_internal_save.mock_calls, [])