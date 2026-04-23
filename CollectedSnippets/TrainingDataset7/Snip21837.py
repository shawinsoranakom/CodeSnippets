def test_list_relative_path(self):
        self.storage.save("a/file.txt", ContentFile("test"))

        _dirs, files = self.storage.listdir("./a/./.")
        self.assertEqual(files, ["file.txt"])