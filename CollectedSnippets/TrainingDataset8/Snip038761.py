def test_maybe_convert_to_wave_numpy_arr_empty(self):
        """Test _maybe_convert_to_wave_bytes works correctly with empty numpy array."""
        sample_rate = 44100
        fake_audio_np_array = np.array([])

        computed_bytes = _maybe_convert_to_wav_bytes(
            fake_audio_np_array, sample_rate=sample_rate
        )

        self.assertEqual(
            computed_bytes,
            b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00"
            b"\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00",
        )