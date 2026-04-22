def test_added_file_id(self):
        """An added file should have a unique ID."""
        f1 = self.mgr.add_file("session", "widget", FILE_1)
        f2 = self.mgr.add_file("session", "widget", FILE_1)
        self.assertNotEqual(FILE_1.id, f1.id)
        self.assertNotEqual(f1.id, f2.id)