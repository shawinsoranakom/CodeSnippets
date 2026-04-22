def setUp(self):
        super().setUp()
        self.storage = MemoryMediaFileStorage(media_endpoint="/mock/media")