def test_closing_of_filenames(self):
        """
        get_image_dimensions() called with a filename should closed the file.
        """
        # We need to inject a modified open() builtin into the images module
        # that checks if the file was closed properly if the function is
        # called with a filename instead of a file object.
        # get_image_dimensions will call our catching_open instead of the
        # regular builtin one.

        class FileWrapper:
            _closed = []

            def __init__(self, f):
                self.f = f

            def __getattr__(self, name):
                return getattr(self.f, name)

            def close(self):
                self._closed.append(True)
                self.f.close()

        def catching_open(*args):
            return FileWrapper(open(*args))

        images.open = catching_open
        try:
            images.get_image_dimensions(
                os.path.join(os.path.dirname(__file__), "test1.png")
            )
        finally:
            del images.open
        self.assertTrue(FileWrapper._closed)