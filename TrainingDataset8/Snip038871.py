def test_st_image_bad_width(self):
        """Test st.image with bad width."""
        with self.assertRaises(StreamlitAPIException) as ctx:
            st.image("does/not/exist", width=-1234)

        self.assertTrue("Image width must be positive." in str(ctx.exception))