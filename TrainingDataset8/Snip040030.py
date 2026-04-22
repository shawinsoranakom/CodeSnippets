def setUp(self):
        self.mgr = UploadedFileManager()
        self.filemgr_events = []
        self.mgr.on_files_updated.connect(self._on_files_updated)