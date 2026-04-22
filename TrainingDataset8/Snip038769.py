def test_st_audio_from_none(self):
        """st.audio(None) is not an error."""
        st.audio(None)
        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.audio.url, "")