def test_remove_session_files(self):
        # This should not error.
        self.mgr.remove_session_files("non-report")

        # Add two files with different session IDs, but the same widget ID.
        self.mgr.add_file("session1", "widget1", FILE_1)
        self.mgr.add_file("session1", "widget2", FILE_1)
        f3 = self.mgr.add_file("session2", "widget", FILE_1)

        self.mgr.remove_session_files("session1")
        self.assertEqual([], self.mgr.get_all_files("session1", "widget1"))
        self.assertEqual([], self.mgr.get_all_files("session1", "widget2"))
        self.assertEqual([f3], self.mgr.get_all_files("session2", "widget"))