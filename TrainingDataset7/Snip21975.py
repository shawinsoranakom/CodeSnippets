def test_no_parsing_triggered_by_fd_closing(self):
        file = tempfile.NamedTemporaryFile
        with file() as f1, file() as f2a, file() as f2b:
            response = self.client.post(
                "/fd_closing/f/",
                {
                    "file": f1,
                    "file2": (f2a, f2b),
                },
            )

        request = response.wsgi_request
        # The fd closing logic doesn't trigger parsing of the stream
        self.assertFalse(hasattr(request, "_files"))