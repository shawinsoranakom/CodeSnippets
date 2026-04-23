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