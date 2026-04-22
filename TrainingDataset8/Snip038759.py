def test_st_audio_missing_sample_rate_numpy_arr(self):
        """Test st.audio raises exception when sample_rate missing in case of valid
        numpy array."""

        valid_np_array = np.array([1, 2, 3, 4, 5])

        with self.assertRaises(StreamlitAPIException) as e:
            st.audio(valid_np_array)

        self.assertEqual(
            str(e.exception),
            "`sample_rate` must be specified when `data` is a numpy array.",
        )