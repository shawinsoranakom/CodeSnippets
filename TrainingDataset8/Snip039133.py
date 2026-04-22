def test_st_video_from_bytes(self):
        """Test st.video using fake bytes data."""
        # Make up some bytes to pretend we have a video.  The server should not vet
        # the video before sending it to the browser.
        fake_video_data = "\x12\x10\x35\x44\x55\x66".encode("utf-8")

        st.video(fake_video_data)

        el = self.get_delta_from_queue().new_element

        # locate resultant file in InMemoryFileManager and test its properties.
        file_id = _calculate_file_id(fake_video_data, "video/mp4")
        media_file = self.media_file_storage.get_file(file_id)
        self.assertIsNotNone(media_file)
        self.assertEqual(media_file.mimetype, "video/mp4")
        self.assertEqual(self.media_file_storage.get_url(file_id), el.video.url)