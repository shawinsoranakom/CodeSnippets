def test_remove_session_files(self):
        """`remove_session_files` is thread-safe."""
        # Add a bunch of files, each to a different session
        file_ids = []
        for ii in range(self.NUM_THREADS):
            file = UploadedFileRec(id=0, name=f"file_{ii}", type="type", data=b"123")
            file_ids.append(self.mgr.add_file(f"session_{ii}", "widget", file).id)

        # Have each thread remove its session's file
        def remove_session_files(index: int) -> None:
            session_id = f"session_{index}"
            # Our file should exist
            session_files = self.mgr.get_all_files(session_id, "widget")
            self.assertEqual(1, len(session_files))
            self.assertEqual(file_ids[index], session_files[0].id)

            # Remove session files
            self.mgr.remove_session_files(session_id)

            # Our file should no longer exist
            session_files = self.mgr.get_all_files(session_id, "widget")
            self.assertEqual(0, len(session_files))

        call_on_threads(remove_session_files, num_threads=self.NUM_THREADS)