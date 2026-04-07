def test_corrupted_image(self):
        f = ImageField()
        img_file = SimpleUploadedFile("not_an_image.jpg", b"not an image")
        msg = (
            "Upload a valid image. The file you uploaded was either not an "
            "image or a corrupted image."
        )
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean(img_file)
        with TemporaryUploadedFile(
            "not_an_image_tmp.png", "text/plain", 1, "utf-8"
        ) as tmp_file:
            with self.assertRaisesMessage(ValidationError, msg):
                f.clean(tmp_file)