def test_temp_directory(self, dir):
        """Test that the directory only exists inside the context."""
        with TemporaryDirectory(dir=dir.path) as temp_fname:
            self.assertTrue(os.path.exists(temp_fname))
        self.assertFalse(os.path.exists(temp_fname))