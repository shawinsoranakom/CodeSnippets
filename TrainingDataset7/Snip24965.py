def assertNotRecentlyModified(self, path):
        """
        Assert that file was not recently modified (modification time was more
        than 10 seconds ago).
        """
        delta = time.time() - os.stat(path).st_mtime
        self.assertGreater(delta, 10, "%s wasn't recently modified" % path)