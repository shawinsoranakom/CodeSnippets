def test_pathlib_upload_to(self):
        obj = Storage()
        obj.pathlib_callable.save("some_file1.txt", ContentFile("some content"))
        self.assertEqual(obj.pathlib_callable.name, "bar/some_file1.txt")
        obj.pathlib_direct.save("some_file2.txt", ContentFile("some content"))
        self.assertEqual(obj.pathlib_direct.name, "bar/some_file2.txt")
        obj.random.close()