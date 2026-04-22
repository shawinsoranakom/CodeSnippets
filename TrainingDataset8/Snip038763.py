def test_maybe_convert_to_wave_numpy_arr_stereo(self):
        """Test _maybe_convert_to_wave_bytes works correctly with 2d numpy array."""
        sample_rate = 44100
        left_channel = np.array([1, 9])
        right_channel = np.array([6, 1])

        fake_audio_np_array = np.array([left_channel, right_channel])

        computed_bytes = _maybe_convert_to_wav_bytes(
            fake_audio_np_array, sample_rate=sample_rate
        )

        self.assertEqual(
            computed_bytes,
            b"RIFF,\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x02\x00D\xac\x00\x00"
            b"\x10\xb1\x02\x00\x04\x00\x10\x00data\x08\x00\x00\x008\x0eTU\xff\x7f8\x0e",
        )