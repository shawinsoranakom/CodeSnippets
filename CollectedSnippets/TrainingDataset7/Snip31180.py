def test_content_length_file(self):
        response = FileResponse(open(__file__, "rb"))
        response.close()
        self.assertEqual(
            response.headers["Content-Length"], str(os.path.getsize(__file__))
        )