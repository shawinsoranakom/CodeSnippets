def test_filefield_read(self):
        # Files can be read in a little at a time, if necessary.
        obj = Storage.objects.create(
            normal=SimpleUploadedFile("assignment.txt", b"content")
        )
        obj.normal.open()
        self.assertEqual(obj.normal.read(3), b"con")
        self.assertEqual(obj.normal.read(), b"tent")
        self.assertEqual(
            list(obj.normal.chunks(chunk_size=2)), [b"co", b"nt", b"en", b"t"]
        )
        obj.normal.close()