def test_st_audio_from_url(self):
        """We can pass a URL directly to st.audio."""
        # Test using a URL instead of data
        some_url = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3"
        st.audio(some_url)

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.audio.url, some_url)