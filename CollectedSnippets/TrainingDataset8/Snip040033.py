def test_added_file_properties(self):
        """An added file should maintain all its source properties
        except its ID."""
        added = self.mgr.add_file("session", "widget", FILE_1)
        self.assertNotEqual(added.id, FILE_1.id)
        self.assertEqual(added.name, FILE_1.name)
        self.assertEqual(added.type, FILE_1.type)
        self.assertEqual(added.data, FILE_1.data)