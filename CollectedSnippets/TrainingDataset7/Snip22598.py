def test_imagefield_annotate_with_image_after_clean(self):
        f = ImageField()

        img_path = get_img_path("filepath_test_files/1x1.png")
        with open(img_path, "rb") as img_file:
            img_data = img_file.read()

        img_file = SimpleUploadedFile("1x1.png", img_data)
        img_file.content_type = "text/plain"

        uploaded_file = f.clean(img_file)

        self.assertEqual("PNG", uploaded_file.image.format)
        self.assertEqual("image/png", uploaded_file.content_type)