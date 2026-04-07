def test_broken_symlink(self):
        """
        Test broken symlink gets deleted.
        """
        path = os.path.join(settings.STATIC_ROOT, "test.txt")
        os.unlink(path)
        self.run_collectstatic()
        self.assertTrue(os.path.islink(path))