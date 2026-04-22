def test_st_video_from_none(self):
        """st.video(None) is not an error."""
        st.video(None)
        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.video.url, "")