def test_maybe_convert_to_wave_bytes_without_sample_rate(self):
        """Test _maybe_convert_to_wave_bytes works correctly when sample_rate
        is None."""

        np_arr = np.array([0, 1, 2, 3])
        computed_bytes = _maybe_convert_to_wav_bytes(np_arr, sample_rate=None)
        self.assertTrue(computed_bytes is np_arr)