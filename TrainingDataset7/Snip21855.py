def test_empty_location(self):
        """
        Makes sure an exception is raised if the location is empty
        """
        storage = self.storage_class(location="")
        self.assertEqual(storage.base_location, "")
        self.assertEqual(storage.location, os.getcwd())