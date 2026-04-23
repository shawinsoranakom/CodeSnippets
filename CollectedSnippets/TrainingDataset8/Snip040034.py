def test_retrieve_added_file(self):
        """After adding a file to the mgr, we should be able to get it back."""
        self.assertEqual([], self.mgr.get_all_files("non-report", "non-widget"))

        file_1 = self.mgr.add_file("session", "widget", FILE_1)
        self.assertEqual([file_1], self.mgr.get_all_files("session", "widget"))
        self.assertEqual([file_1], self.mgr.get_files("session", "widget", [file_1.id]))
        self.assertEqual(len(self.filemgr_events), 1)

        # Add another file
        file_2 = self.mgr.add_file("session", "widget", FILE_2)
        self.assertEqual([file_1, file_2], self.mgr.get_all_files("session", "widget"))
        self.assertEqual([file_1], self.mgr.get_files("session", "widget", [file_1.id]))
        self.assertEqual([file_2], self.mgr.get_files("session", "widget", [file_2.id]))
        self.assertEqual(len(self.filemgr_events), 2)