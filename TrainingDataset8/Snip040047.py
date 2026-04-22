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