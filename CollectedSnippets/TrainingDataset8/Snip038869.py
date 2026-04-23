def test_st_image_with_single_url(self):
        """Test st.image with single url."""
        url = "http://server/fake0.jpg"

        st.image(url, caption="some caption", width=300)

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.imgs.width, 300)
        self.assertEqual(el.imgs.imgs[0].caption, "some caption")
        self.assertEqual(el.imgs.imgs[0].url, url)