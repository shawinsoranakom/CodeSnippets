def test_content_file_custom_name(self):
        """
        The constructor of ContentFile accepts 'name' (#16590).
        """
        name = "I can have a name too!"
        self.assertEqual(ContentFile(b"content", name=name).name, name)