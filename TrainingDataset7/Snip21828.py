def test_write_string(self):
        with self.storage.open("file.txt", "w") as fd:
            fd.write("hello")
        with self.storage.open("file.txt", "r") as fd:
            self.assertEqual(fd.read(), "hello")
        with self.storage.open("file.dat", "wb") as fd:
            fd.write(b"hello")
        with self.storage.open("file.dat", "rb") as fd:
            self.assertEqual(fd.read(), b"hello")