def test_file_saving(self):
        self.storage.save("file.txt", ContentFile("test"))
        self.assertEqual(self.storage.open("file.txt", "r").read(), "test")

        self.storage.save("file.dat", ContentFile(b"test"))
        self.assertEqual(self.storage.open("file.dat", "rb").read(), b"test")