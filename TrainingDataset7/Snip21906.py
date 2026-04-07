def test_random_upload_to(self):
        # Verify the fix for #5655, making sure the directory is only
        # determined once.
        obj = Storage()
        obj.random.save("random_file", ContentFile("random content"))
        self.assertTrue(obj.random.name.endswith("/random_file"))
        obj.random.close()