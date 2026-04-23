def __init__(self, *args, manifest_storage=None, **kwargs):
        super().__init__(*args, **kwargs)
        if manifest_storage is None:
            manifest_storage = self
        self.manifest_storage = manifest_storage
        self.hashed_files, self.manifest_hash = self.load_manifest()