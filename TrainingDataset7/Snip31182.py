def test_content_length_nonzero_starting_position_file(self):
        file = open(__file__, "rb")
        file.seek(10)
        response = FileResponse(file)
        response.close()
        self.assertEqual(
            response.headers["Content-Length"], str(os.path.getsize(__file__) - 10)
        )