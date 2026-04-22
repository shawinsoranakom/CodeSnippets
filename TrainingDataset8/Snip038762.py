def test_maybe_convert_to_wave_numpy_arr_mono(self):
        """Test _maybe_convert_to_wave_bytes works correctly with 1d numpy array."""
        sample_rate = 7
        fake_audio_np_array = np.array([1, 9])

        computed_bytes = _maybe_convert_to_wav_bytes(
            fake_audio_np_array, sample_rate=sample_rate
        )

        self.assertEqual(
            computed_bytes,
            b"RIFF(\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x07\x00\x00"
            b"\x00\x0e\x00\x00\x00\x02\x00\x10\x00data\x04\x00\x00\x008\x0e\xff\x7f",
        )