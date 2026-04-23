def test_st_video_from_url(self):
        """We can pass a URL directly to st.video"""
        some_url = "http://www.marmosetcare.com/video/in-the-wild/intro.webm"
        st.video(some_url)
        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.video.url, some_url)