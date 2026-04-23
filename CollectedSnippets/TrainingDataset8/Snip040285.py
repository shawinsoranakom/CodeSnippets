def setUp(self) -> None:
        super().setUp()
        # Create a new MediaFileManager and assign its storage to
        # MediaFileHandler.
        storage = MemoryMediaFileStorage(MOCK_ENDPOINT)
        self.media_file_manager = MediaFileManager(storage)
        MediaFileHandler.initialize_storage(storage)