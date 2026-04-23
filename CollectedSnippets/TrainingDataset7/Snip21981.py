def test_readonly_root(self):
        """Permission errors are not swallowed"""
        os.chmod(MEDIA_ROOT, 0o500)
        self.addCleanup(os.chmod, MEDIA_ROOT, 0o700)
        with self.assertRaises(PermissionError):
            self.obj.testfile.save(
                "foo.txt", SimpleUploadedFile("foo.txt", b"x"), save=False
            )