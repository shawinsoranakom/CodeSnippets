def setUp(self):
        super().setUp()
        self.finder = finders.DefaultStorageFinder(
            storage=storage.StaticFilesStorage(location=settings.MEDIA_ROOT)
        )
        test_file_path = os.path.join(settings.MEDIA_ROOT, "media-file.txt")
        self.find_first = ("media-file.txt", test_file_path)
        self.find_all = ("media-file.txt", [test_file_path])