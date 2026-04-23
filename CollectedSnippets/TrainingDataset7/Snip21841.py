def test_file_node_cannot_have_children(self):
        """Navigate to children of a file node raises FileExistsError."""
        self.storage.save("file.txt", ContentFile("test"))
        self.assertRaises(FileExistsError, self.storage.listdir, "file.txt/child_dir")
        self.assertRaises(
            FileExistsError,
            self.storage.save,
            "file.txt/child_file.txt",
            ContentFile("test"),
        )