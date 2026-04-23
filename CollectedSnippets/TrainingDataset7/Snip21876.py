def test_makedirs_race_handling(self):
        """
        File storage should be robust against directory creation race
        conditions.
        """
        real_makedirs = os.makedirs

        # Monkey-patch os.makedirs, to simulate a normal call, a raced call,
        # and an error.
        def fake_makedirs(path, mode=0o777, exist_ok=False):
            if path == os.path.join(self.temp_dir, "normal"):
                real_makedirs(path, mode, exist_ok)
            elif path == os.path.join(self.temp_dir, "raced"):
                real_makedirs(path, mode, exist_ok)
                if not exist_ok:
                    raise FileExistsError()
            elif path == os.path.join(self.temp_dir, "error"):
                raise PermissionError()
            else:
                self.fail("unexpected argument %r" % path)

        try:
            os.makedirs = fake_makedirs

            self.storage.save("normal/test.file", ContentFile("saved normally"))
            with self.storage.open("normal/test.file") as f:
                self.assertEqual(f.read(), b"saved normally")

            self.storage.save("raced/test.file", ContentFile("saved with race"))
            with self.storage.open("raced/test.file") as f:
                self.assertEqual(f.read(), b"saved with race")

            # Exceptions aside from FileExistsError are raised.
            with self.assertRaises(PermissionError):
                self.storage.save("error/test.file", ContentFile("not saved"))
        finally:
            os.makedirs = real_makedirs