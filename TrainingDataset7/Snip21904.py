def test_empty_upload_to(self):
        # upload_to can be empty, meaning it does not use subdirectory.
        obj = Storage()
        obj.empty.save("django_test.txt", ContentFile("more content"))
        self.assertEqual(obj.empty.name, "django_test.txt")
        self.assertEqual(obj.empty.read(), b"more content")
        obj.empty.close()