def test_remove_race_handling(self):
        """
        File storage should be robust against file removal race conditions.
        """
        real_remove = os.remove

        # Monkey-patch os.remove, to simulate a normal call, a raced call,
        # and an error.
        def fake_remove(path):
            if path == os.path.join(self.temp_dir, "normal.file"):
                real_remove(path)
            elif path == os.path.join(self.temp_dir, "raced.file"):
                real_remove(path)
                raise FileNotFoundError()
            elif path == os.path.join(self.temp_dir, "error.file"):
                raise PermissionError()
            else:
                self.fail("unexpected argument %r" % path)

        try:
            os.remove = fake_remove

            self.storage.save("normal.file", ContentFile("delete normally"))
            self.storage.delete("normal.file")
            self.assertFalse(self.storage.exists("normal.file"))

            self.storage.save("raced.file", ContentFile("delete with race"))
            self.storage.delete("raced.file")
            self.assertFalse(self.storage.exists("normal.file"))

            # Exceptions aside from FileNotFoundError are raised.
            self.storage.save("error.file", ContentFile("delete with error"))
            with self.assertRaises(PermissionError):
                self.storage.delete("error.file")
        finally:
            os.remove = real_remove