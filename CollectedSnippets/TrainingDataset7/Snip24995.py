def test_no_duplicate_write_po_file_calls(self):
        with mock.patch.object(
            MakeMessagesCommand, "write_po_file"
        ) as mock_write_po_file:
            cmd = MakeMessagesCommand()
            management.call_command(cmd, locale=["en", "ru"], verbosity=0)
            self.assertEqual(
                len(mock_write_po_file.call_args_list),
                len({call.args for call in mock_write_po_file.call_args_list}),
            )