def test_content_saving(self):
        """
        ContentFile can be saved correctly with the filesystem storage,
        if it was initialized with either bytes or unicode content.
        """
        self.storage.save("bytes.txt", ContentFile(b"content"))
        self.storage.save("unicode.txt", ContentFile("español"))