def test_st_image_with_list_of_urls(self):
        """Test st.image with list of urls."""
        urls = [
            "http://server/fake0.jpg",
            "http://server/fake1.png",
            "http://server/fake2.gif",
        ]
        st.image(urls, caption=["some caption"] * 3, width=300)

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.imgs.width, 300)
        for idx, url in enumerate(urls):
            self.assertEqual(el.imgs.imgs[idx].caption, "some caption")
            self.assertEqual(el.imgs.imgs[idx].url, url)