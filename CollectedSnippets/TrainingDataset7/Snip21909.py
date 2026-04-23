def test_file_object(self):
        # Create sample file
        temp_storage.save("tests/example.txt", ContentFile("some content"))

        # Load it as Python file object
        with open(temp_storage.path("tests/example.txt")) as file_obj:
            # Save it using storage and read its content
            temp_storage.save("tests/file_obj", file_obj)
        self.assertTrue(temp_storage.exists("tests/file_obj"))
        with temp_storage.open("tests/file_obj") as f:
            self.assertEqual(f.read(), b"some content")