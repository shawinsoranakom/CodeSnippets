def test_remove_widget_files(self):
        # This should not error.
        self.mgr.remove_session_files("non-report")

        # Add two files with different session IDs, but the same widget ID.
        self.mgr.add_file("session1", "widget", FILE_1)
        f2 = self.mgr.add_file("session2", "widget", FILE_1)

        self.mgr.remove_files("session1", "widget")
        self.assertEqual([], self.mgr.get_all_files("session1", "widget"))
        self.assertEqual([f2], self.mgr.get_all_files("session2", "widget"))