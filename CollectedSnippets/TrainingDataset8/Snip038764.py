def test_maybe_convert_to_wave_bytes_with_sample_rate(self):
        """Test _maybe_convert_to_wave_bytes works correctly with bytes."""

        fake_audio_data_bytes = "\x11\x22\x33\x44\x55\x66".encode("utf-8")
        sample_rate = 44100

        computed_bytes = _maybe_convert_to_wav_bytes(
            fake_audio_data_bytes, sample_rate=sample_rate
        )

        self.assertEqual(computed_bytes, fake_audio_data_bytes)