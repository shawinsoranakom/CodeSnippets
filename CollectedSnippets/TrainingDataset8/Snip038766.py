def test_st_audio_from_file(self):
        """Test st.audio using generated data in a file-like object."""
        sample_rate = 44100
        frequency = 440
        length = 5

        # Produces a 5 second Audio-File
        t = np.linspace(0, length, sample_rate * length)
        # Has frequency of 440Hz
        y = np.sin(frequency * 2 * np.pi * t)

        wavfile.write("test.wav", sample_rate, y)

        with io.open("test.wav", "rb") as f:
            st.audio(f)

        el = self.get_delta_from_queue().new_element
        self.assertTrue(".wav" in el.audio.url)

        os.remove("test.wav")