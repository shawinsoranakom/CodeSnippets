def test_st_audio_other_inputs(self):
        """Test that our other data types don't result in an error."""
        st.audio(b"bytes_data")
        st.audio("str_data".encode("utf-8"))
        st.audio(BytesIO(b"bytesio_data"))
        st.audio(np.array([0, 1, 2, 3]), sample_rate=44100)