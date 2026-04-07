def test_media_root_pathlib(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with override_settings(MEDIA_ROOT=Path(tmp_dir)):
                with TemporaryUploadedFile(
                    "foo.txt", "text/plain", 1, "utf-8"
                ) as tmp_file:
                    document = Document.objects.create(myfile=tmp_file)
                    self.assertIs(
                        document.myfile.storage.exists(
                            os.path.join("unused", "foo.txt")
                        ),
                        True,
                    )