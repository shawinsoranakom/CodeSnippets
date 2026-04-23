def test_content_length_nonzero_starting_position_file_seekable_no_tell(self):
        class TestFile:
            def __init__(self, path, *args, **kwargs):
                self._file = open(path, *args, **kwargs)

            def read(self, n_bytes=-1):
                return self._file.read(n_bytes)

            def seek(self, offset, whence=io.SEEK_SET):
                return self._file.seek(offset, whence)

            def seekable(self):
                return True

            @property
            def name(self):
                return self._file.name

            def close(self):
                if self._file:
                    self._file.close()
                    self._file = None

            def __enter__(self):
                return self

            def __exit__(self, e_type, e_val, e_tb):
                self.close()

        file = TestFile(__file__, "rb")
        file.seek(10)
        response = FileResponse(file)
        response.close()
        self.assertEqual(
            response.headers["Content-Length"], str(os.path.getsize(__file__) - 10)
        )