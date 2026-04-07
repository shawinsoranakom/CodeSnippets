def test_large_file_saving(self):
        large_file = ContentFile("A" * ContentFile.DEFAULT_CHUNK_SIZE * 3)
        self.storage.save("file.txt", large_file)