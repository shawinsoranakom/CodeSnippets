def test_st_audio_valid_numpy_array(self, arr):
        """Test st.audio using fake audio from empty, 1d, 2d numpy array."""

        sample_rate = 44100

        # Fake audio data: expect the resultant mimetype to be audio default.
        fake_audio_np_array = np.array(arr)

        st.audio(fake_audio_np_array, sample_rate=sample_rate)
        computed_bytes = _maybe_convert_to_wav_bytes(
            fake_audio_np_array, sample_rate=sample_rate
        )

        el = self.get_delta_from_queue().new_element

        # locate resultant file in InMemoryFileManager and test its properties.
        file_id = _calculate_file_id(computed_bytes, "audio/wav")
        media_file = self.media_file_storage.get_file(file_id)
        self.assertIsNotNone(media_file)
        self.assertEqual(media_file.mimetype, "audio/wav")
        self.assertEqual(self.media_file_storage.get_url(file_id), el.audio.url)
        self.assertEqual(media_file.content, computed_bytes)