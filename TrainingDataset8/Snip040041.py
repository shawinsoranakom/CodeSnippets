def test_add_file(self):
        """`add_file` is thread-safe."""
        # Call `add_file` from a bunch of threads
        added_files = []

        def add_file(index: int) -> None:
            file = UploadedFileRec(
                id=0, name=f"file_{index}", type="type", data=bytes(f"{index}", "utf-8")
            )
            added_files.append(self.mgr.add_file("session", f"widget_{index}", file))

        call_on_threads(add_file, num_threads=self.NUM_THREADS)

        # Ensure all our files are present
        for ii in range(self.NUM_THREADS):
            files = self.mgr.get_all_files("session", f"widget_{ii}")
            self.assertEqual(1, len(files))
            self.assertEqual(bytes(f"{ii}", "utf-8"), files[0].data)

        # Ensure all files have unique IDs
        file_ids = set()
        for file_list in self.mgr._files_by_id.values():
            file_ids.update(file.id for file in file_list)
        self.assertEqual(self.NUM_THREADS, len(file_ids))