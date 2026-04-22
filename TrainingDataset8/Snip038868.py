def test_st_image_PIL_array(self):
        """Test st.image with a PIL array."""
        imgs = [
            Image.new("RGB", (64, 64), color="red"),
            Image.new("RGB", (64, 64), color="blue"),
            Image.new("RGB", (64, 64), color="green"),
        ]

        st.image(
            imgs,
            caption=["some caption"] * 3,
            width=200,
            use_column_width=True,
            clamp=True,
            output_format="PNG",
        )

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.imgs.width, -2)

        # locate resultant file in the file manager and check its metadata.
        for idx in range(len(imgs)):
            file_id = _calculate_file_id(
                _PIL_to_bytes(imgs[idx], format="PNG"), "image/png"
            )
            self.assertEqual(el.imgs.imgs[idx].caption, "some caption")
            media_file = self.media_file_storage.get_file(file_id)
            self.assertIsNotNone(media_file)
            self.assertEqual(media_file.mimetype, "image/png")
            self.assertEqual(
                self.media_file_storage.get_url(file_id), el.imgs.imgs[idx].url
            )