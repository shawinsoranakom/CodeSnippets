def test_filefield_db_default(self):
        temp_storage.save("tests/db_default.txt", ContentFile("default content"))
        obj = Storage.objects.create()
        self.assertEqual(obj.db_default.name, "tests/db_default.txt")
        self.assertEqual(obj.db_default.read(), b"default content")
        obj.db_default.close()

        # File is not deleted, even if there are no more objects using it.
        obj.delete()
        s = Storage()
        self.assertEqual(s.db_default.name, "tests/db_default.txt")
        self.assertEqual(s.db_default.read(), b"default content")
        s.db_default.close()