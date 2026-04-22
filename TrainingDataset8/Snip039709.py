def setUp(self):
        super().setUp()
        self.storage = MemoryMediaFileStorage("/mock/endpoint")
        self.media_file_manager = MediaFileManager(self.storage)
        random.seed(1337)