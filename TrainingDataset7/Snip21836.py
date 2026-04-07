def test_listdir(self):
        self.assertEqual(self.storage.listdir(""), ([], []))

        self.storage.save("file_a.txt", ContentFile("test"))
        self.storage.save("file_b.txt", ContentFile("test"))
        self.storage.save("dir/file_c.txt", ContentFile("test"))

        dirs, files = self.storage.listdir("")
        self.assertEqual(sorted(files), ["file_a.txt", "file_b.txt"])
        self.assertEqual(dirs, ["dir"])