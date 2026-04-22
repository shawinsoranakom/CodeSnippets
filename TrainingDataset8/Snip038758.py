def test_st_audio_invalid_numpy_array(self, np_arr, expected_shape, exception_text):
        """Test st.audio using invalid numpy array."""

        sample_rate = 44100
        self.assertEqual(len(np_arr.shape), expected_shape)

        with self.assertRaises(StreamlitAPIException) as e:
            st.audio(np_arr, sample_rate=sample_rate)

        self.assertEqual(str(e.exception), exception_text)