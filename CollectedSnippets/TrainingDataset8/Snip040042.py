def test_remove_file(self):
        """`remove_file` is thread-safe."""
        # Add a bunch of files to a single widget
        file_ids = []
        for ii in range(self.NUM_THREADS):
            file = UploadedFileRec(id=0, name=f"file_{ii}", type="type", data=b"123")
            file_ids.append(self.mgr.add_file("session", "widget", file).id)

        # Have each thread remove a single file
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

        call_on_threads(remove_file, self.NUM_THREADS)

        self.assertEqual(0, len(self.mgr.get_all_files("session", "widget")))