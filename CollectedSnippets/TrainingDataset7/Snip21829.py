def test_convert_str_to_bytes_and_back(self):
        """InMemoryStorage handles conversion from str to bytes and back."""
        with self.storage.open("file.txt", "w") as fd:
            fd.write("hello")
        with self.storage.open("file.txt", "rb") as fd:
            self.assertEqual(fd.read(), b"hello")
        with self.storage.open("file.dat", "wb") as fd:
            fd.write(b"hello")
        with self.storage.open("file.dat", "r") as fd:
            self.assertEqual(fd.read(), "hello")