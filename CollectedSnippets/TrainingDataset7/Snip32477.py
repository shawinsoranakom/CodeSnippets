def test_symlinks_and_files_replaced(self):
        """
        Running collectstatic in non-symlink mode replaces symlinks with files,
        while symlink mode replaces files with symlinks.
        """
        path = os.path.join(settings.STATIC_ROOT, "test.txt")
        self.assertTrue(os.path.islink(path))
        self.run_collectstatic(link=False)
        self.assertFalse(os.path.islink(path))
        self.run_collectstatic(link=True)
        self.assertTrue(os.path.islink(path))