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