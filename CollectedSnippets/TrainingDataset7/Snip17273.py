def test_singleton_main(self):
        """
        Only one main registry can exist.
        """
        with self.assertRaises(RuntimeError):
            Apps(installed_apps=None)