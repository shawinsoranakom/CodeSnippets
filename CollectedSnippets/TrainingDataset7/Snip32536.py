def setUp(self):
        manifest_path = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, manifest_path)

        self.staticfiles_storage = CustomManifestStorage(
            manifest_location=manifest_path,
        )
        self.manifest_file = manifest_path / self.staticfiles_storage.manifest_name
        # Manifest without paths.
        self.manifest = {"version": self.staticfiles_storage.manifest_version}
        with self.manifest_file.open("w") as manifest_file:
            json.dump(self.manifest, manifest_file)