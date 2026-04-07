def test_imagefield_annotate_with_bitmap_image_after_clean(self):
        """
        This also tests the situation when Pillow doesn't detect the MIME type
        of the image (#24948).
        """
        from PIL.BmpImagePlugin import BmpImageFile

        try:
            Image.register_mime(BmpImageFile.format, None)
            f = ImageField()
            img_path = get_img_path("filepath_test_files/1x1.bmp")
            with open(img_path, "rb") as img_file:
                img_data = img_file.read()

            img_file = SimpleUploadedFile("1x1.bmp", img_data)
            img_file.content_type = "text/plain"

            uploaded_file = f.clean(img_file)

            self.assertEqual("BMP", uploaded_file.image.format)
            self.assertIsNone(uploaded_file.content_type)
        finally:
            Image.register_mime(BmpImageFile.format, "image/bmp")