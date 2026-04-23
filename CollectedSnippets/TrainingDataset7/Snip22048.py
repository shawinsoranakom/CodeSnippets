def test_not_closing_of_files(self):
        """
        Open files passed into get_image_dimensions() should stay opened.
        """
        empty_io = BytesIO()
        try:
            images.get_image_dimensions(empty_io)
        finally:
            self.assertTrue(not empty_io.closed)