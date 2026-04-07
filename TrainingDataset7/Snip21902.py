def test_filefield_default(self):
        # Default values allow an object to access a single file.
        temp_storage.save("tests/default.txt", ContentFile("default content"))
        obj = Storage.objects.create()
        self.assertEqual(obj.default.name, "tests/default.txt")
        self.assertEqual(obj.default.read(), b"default content")
        obj.default.close()

        # But it shouldn't be deleted, even if there are no more objects using
        # it.
        obj.delete()
        obj = Storage()
        self.assertEqual(obj.default.read(), b"default content")
        obj.default.close()