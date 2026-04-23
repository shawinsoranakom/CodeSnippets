def test_st_image_PIL_image(self):
        """Test st.image with PIL image."""
        img = Image.new("RGB", (64, 64), color="red")

        st.image(img, caption="some caption", width=100, output_format="PNG")

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.imgs.width, 100)
        self.assertEqual(el.imgs.imgs[0].caption, "some caption")

        # locate resultant file in the file manager and check its metadata.
        file_id = _calculate_file_id(_PIL_to_bytes(img, format="PNG"), "image/png")
        media_file = self.media_file_storage.get_file(file_id)
        self.assertIsNotNone(media_file)
        self.assertEqual(media_file.mimetype, "image/png")
        self.assertEqual(self.media_file_storage.get_url(file_id), el.imgs.imgs[0].url)