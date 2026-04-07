def test_file_extension_validation(self):
        f = ImageField()
        img_path = get_img_path("filepath_test_files/1x1.png")
        with open(img_path, "rb") as img_file:
            img_data = img_file.read()
        img_file = SimpleUploadedFile("1x1.txt", img_data)
        with self.assertRaisesMessage(
            ValidationError, "File extension “txt” is not allowed."
        ):
            f.clean(img_file)