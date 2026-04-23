def test_unequal_images_and_captions_error(self):
        """Tests that the number of images and captions must match, or
        an exception is generated"""

        url = "https://streamlit.io/an_image.png"
        caption = "ahoy!"

        with self.assertRaises(Exception) as ctx:
            st.image([url] * 5, caption=[caption] * 2)
        self.assertTrue("Cannot pair 2 captions with 5 images." in str(ctx.exception))