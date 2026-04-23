def test_filefield_write(self):
        # Files can be written to.
        obj = Storage.objects.create(
            normal=SimpleUploadedFile("rewritten.txt", b"content")
        )
        with obj.normal as normal:
            normal.open("wb")
            normal.write(b"updated")
        obj.refresh_from_db()
        self.assertEqual(obj.normal.read(), b"updated")
        obj.normal.close()