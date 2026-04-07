def test_links_created(self):
        """
        With ``--link``, symbolic links are created.
        """
        self.assertTrue(os.path.islink(os.path.join(settings.STATIC_ROOT, "test.txt")))