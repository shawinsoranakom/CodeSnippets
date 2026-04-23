def test_st_audio_raises_on_bad_filename(self):
        """A non-URL string is assumed to be a filename. A file we can't
        open will result in an error.
        """
        with self.assertRaises(MediaFileStorageError):
            st.audio("not/a/real/file")