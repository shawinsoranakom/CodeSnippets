def assertRecentlyModified(self, path):
        """
        Assert that file was recently modified (modification time was less than
        10 seconds ago).
        """
        delta = time.time() - os.stat(path).st_mtime
        self.assertLess(delta, 10, "%s was recently modified" % path)