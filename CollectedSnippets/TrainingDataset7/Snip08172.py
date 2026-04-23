def save_manifest(self):
        sorted_hashed_files = sorted(self.hashed_files.items())
        self.manifest_hash = self.file_hash(
            None, ContentFile(json.dumps(sorted_hashed_files).encode())
        )
        payload = {
            "paths": dict(sorted_hashed_files),
            "version": self.manifest_version,
            "hash": self.manifest_hash,
        }
        if self.manifest_storage.exists(self.manifest_name):
            self.manifest_storage.delete(self.manifest_name)
        contents = json.dumps(payload).encode()
        self.manifest_storage._save(self.manifest_name, ContentFile(contents))