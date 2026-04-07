def test_charset_detection(self):
        """HttpResponse should parse charset from content_type."""
        response = HttpResponse("ok")
        self.assertEqual(response.charset, settings.DEFAULT_CHARSET)

        response = HttpResponse(charset=ISO88591)
        self.assertEqual(response.charset, ISO88591)
        self.assertEqual(
            response.headers["Content-Type"], "text/html; charset=%s" % ISO88591
        )

        response = HttpResponse(
            content_type="text/plain; charset=%s" % UTF8, charset=ISO88591
        )
        self.assertEqual(response.charset, ISO88591)

        response = HttpResponse(content_type="text/plain; charset=%s" % ISO88591)
        self.assertEqual(response.charset, ISO88591)

        response = HttpResponse(content_type='text/plain; charset="%s"' % ISO88591)
        self.assertEqual(response.charset, ISO88591)

        response = HttpResponse(content_type="text/plain; charset=")
        self.assertEqual(response.charset, settings.DEFAULT_CHARSET)

        response = HttpResponse(content_type="text/plain")
        self.assertEqual(response.charset, settings.DEFAULT_CHARSET)