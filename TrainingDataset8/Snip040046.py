def remove_file(index: int) -> None:
            file_id = file_ids[index]

            # Ensure our file exists
            get_files_result = self.mgr.get_files("session", "widget", [file_id])
            self.assertEqual(1, len(get_files_result))

            # Remove our file
            was_removed = self.mgr.remove_file("session", "widget", file_id)
            self.assertTrue(was_removed)

            # Ensure our file no longer exists
            get_files_result = self.mgr.get_files("session", "widget", [file_id])
            self.assertEqual(0, len(get_files_result))