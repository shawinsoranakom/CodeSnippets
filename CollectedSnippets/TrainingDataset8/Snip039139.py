def test_st_video_options(self):
        """Test st.video with options."""
        fake_video_data = "\x11\x22\x33\x44\x55\x66".encode("utf-8")
        st.video(fake_video_data, format="video/mp4", start_time=10)

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.video.start_time, 10)
        self.assertTrue(el.video.url.startswith(MEDIA_ENDPOINT))
        self.assertTrue(
            _calculate_file_id(fake_video_data, "video/mp4") in el.video.url
        )