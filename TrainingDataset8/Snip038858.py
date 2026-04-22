def test_marshall_images_with_auto_output_format(
        self, data_in: image.AtomicImage, expected_extension: str
    ):
        """Test streamlit.image.marshall_images.
        with auto output_format
        """

        st.image(data_in, output_format="auto")
        imglist = self.get_delta_from_queue().new_element.imgs
        self.assertEqual(len(imglist.imgs), 1)
        self.assertTrue(imglist.imgs[0].url.endswith(expected_extension))