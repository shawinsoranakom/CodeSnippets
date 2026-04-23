def test_st_audio_sample_rate_raises_warning(self):
        """Test st.audio raises streamlit warning when sample_rate parameter provided,
        but data is not a numpy array."""

        fake_audio_data = "\x11\x22\x33\x44\x55\x66".encode("utf-8")
        sample_rate = 44100

        st.audio(fake_audio_data, sample_rate=sample_rate)

        c = self.get_delta_from_queue(-2).new_element.alert
        self.assertEqual(c.format, AlertProto.WARNING)
        self.assertEqual(
            c.body,
            "Warning: `sample_rate` will be ignored since data is not a numpy array.",
        )