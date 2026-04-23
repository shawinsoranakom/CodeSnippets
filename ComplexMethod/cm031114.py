def do_test(test, obj, abilities):
            readable = "r" in abilities
            self.assertEqual(obj.readable(), readable)
            writable = "w" in abilities
            self.assertEqual(obj.writable(), writable)

            if isinstance(obj, self.TextIOBase):
                data = "3"
            elif isinstance(obj, (self.BufferedIOBase, self.RawIOBase)):
                data = b"3"
            else:
                self.fail("Unknown base class")

            if "f" in abilities:
                obj.fileno()
            else:
                self.assertRaises(OSError, obj.fileno)

            if readable:
                obj.read(1)
                obj.read()
            else:
                self.assertRaises(OSError, obj.read, 1)
                self.assertRaises(OSError, obj.read)

            if writable:
                obj.write(data)
            else:
                self.assertRaises(OSError, obj.write, data)

            if sys.platform.startswith("win") and test in (
                    pipe_reader, pipe_writer):
                # Pipes seem to appear as seekable on Windows
                return
            seekable = "s" in abilities
            self.assertEqual(obj.seekable(), seekable)

            if seekable:
                obj.tell()
                obj.seek(0)
            else:
                self.assertRaises(OSError, obj.tell)
                self.assertRaises(OSError, obj.seek, 0)

            if writable and seekable:
                obj.truncate()
                obj.truncate(0)
            else:
                self.assertRaises(OSError, obj.truncate)
                self.assertRaises(OSError, obj.truncate, 0)