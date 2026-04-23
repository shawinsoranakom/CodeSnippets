def test_io_after_close(self):
        for kwargs in [
                {"mode": "w"},
                {"mode": "wb"},
                {"mode": "w", "buffering": 1},
                {"mode": "w", "buffering": 2},
                {"mode": "wb", "buffering": 0},
                {"mode": "r"},
                {"mode": "rb"},
                {"mode": "r", "buffering": 1},
                {"mode": "r", "buffering": 2},
                {"mode": "rb", "buffering": 0},
                {"mode": "w+"},
                {"mode": "w+b"},
                {"mode": "w+", "buffering": 1},
                {"mode": "w+", "buffering": 2},
                {"mode": "w+b", "buffering": 0},
            ]:
            if "b" not in kwargs["mode"]:
                kwargs["encoding"] = "utf-8"
            f = self.open(os_helper.TESTFN, **kwargs)
            f.close()
            self.assertRaises(ValueError, f.flush)
            self.assertRaises(ValueError, f.fileno)
            self.assertRaises(ValueError, f.isatty)
            self.assertRaises(ValueError, f.__iter__)
            if hasattr(f, "peek"):
                self.assertRaises(ValueError, f.peek, 1)
            self.assertRaises(ValueError, f.read)
            if hasattr(f, "read1"):
                self.assertRaises(ValueError, f.read1, 1024)
                self.assertRaises(ValueError, f.read1)
            if hasattr(f, "readall"):
                self.assertRaises(ValueError, f.readall)
            if hasattr(f, "readinto"):
                self.assertRaises(ValueError, f.readinto, bytearray(1024))
            if hasattr(f, "readinto1"):
                self.assertRaises(ValueError, f.readinto1, bytearray(1024))
            self.assertRaises(ValueError, f.readline)
            self.assertRaises(ValueError, f.readlines)
            self.assertRaises(ValueError, f.readlines, 1)
            self.assertRaises(ValueError, f.seek, 0)
            self.assertRaises(ValueError, f.tell)
            self.assertRaises(ValueError, f.truncate)
            self.assertRaises(ValueError, f.write,
                              b"" if "b" in kwargs['mode'] else "")
            self.assertRaises(ValueError, f.writelines, [])
            self.assertRaises(ValueError, next, f)