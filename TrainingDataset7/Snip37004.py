def test_error_pages(self):
        request = self.request_factory.get("/")
        for response, title in (
            (bad_request(request, Exception()), b"Bad Request (400)"),
            (permission_denied(request, Exception()), b"403 Forbidden"),
            (page_not_found(request, Http404()), b"Not Found"),
            (server_error(request), b"Server Error (500)"),
        ):
            with self.subTest(title=title):
                self.assertIn(b"<!doctype html>", response.content)
                self.assertIn(b'<html lang="en">', response.content)
                self.assertIn(b"<head>", response.content)
                self.assertIn(b"<title>%s</title>" % title, response.content)
                self.assertIn(b"<body>", response.content)