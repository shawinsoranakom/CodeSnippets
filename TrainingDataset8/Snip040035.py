def test_remove_file(self):
        # This should not error.
        self.mgr.remove_files("non-report", "non-widget")

        f1 = self.mgr.add_file("session", "widget", FILE_1)
        self.mgr.remove_file("session", "widget", f1.id)
        self.assertEqual([], self.mgr.get_all_files("session", "widget"))

        # Remove the file again. It doesn't exist, but this isn't an error.
        self.mgr.remove_file("session", "widget", f1.id)
        self.assertEqual([], self.mgr.get_all_files("session", "widget"))

        f1 = self.mgr.add_file("session", "widget", FILE_1)
        f2 = self.mgr.add_file("session", "widget", FILE_2)
        self.mgr.remove_file("session", "widget", f1.id)
        self.assertEqual([f2], self.mgr.get_all_files("session", "widget"))