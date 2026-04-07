def test_unicode_uploadedfile_name(self):
        uf = UploadedFile(name="¿Cómo?", content_type="text")
        self.assertIs(type(repr(uf)), str)