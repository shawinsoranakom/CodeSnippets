def test_file_size(self):
        """
        File size is equal to the size of bytes-encoded version of the saved
        data.
        """
        self.storage.save("file.txt", ContentFile("test"))
        self.assertEqual(self.storage.size("file.txt"), 4)

        # A unicode char encoded to UTF-8 takes 2 bytes.
        self.storage.save("unicode_file.txt", ContentFile("è"))
        self.assertEqual(self.storage.size("unicode_file.txt"), 2)

        self.storage.save("file.dat", ContentFile(b"\xf1\xf1"))
        self.assertEqual(self.storage.size("file.dat"), 2)