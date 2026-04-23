def test_filefield_reopen(self):
        obj = Storage.objects.create(
            normal=SimpleUploadedFile("reopen.txt", b"content")
        )
        with obj.normal as normal:
            normal.open()
        obj.normal.open()
        obj.normal.file.seek(0)
        obj.normal.close()