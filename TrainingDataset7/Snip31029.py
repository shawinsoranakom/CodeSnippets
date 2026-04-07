def test_quality_for_media_type_rfc7231(self):
        """
        Taken from https://datatracker.ietf.org/doc/html/rfc7231#section-5.3.2.
        """
        request = HttpRequest()
        request.META["HTTP_ACCEPT"] = (
            "text/*;q=0.3,text/html;q=0.7,text/html;level=1,text/html;level=2;q=0.4,"
            "*/*;q=0.5"
        )

        for media_type, quality in [
            ("text/html;level=1", 1),
            ("text/html", 0.7),
            ("text/plain", 0.3),
            ("image/jpeg", 0.5),
            ("text/html;level=2", 0.4),
            ("text/html;level=3", 0.7),
        ]:
            with self.subTest(media_type):
                accepted_media_type = request.accepted_type(media_type)
                self.assertIsNotNone(accepted_media_type)
                self.assertEqual(accepted_media_type.quality, quality)

        for media_types, expected in [
            (["text/html", "text/html; level=1"], "text/html; level=1"),
            (["text/html; level=2", "text/html; level=3"], "text/html; level=3"),
        ]:
            self.assertEqual(request.get_preferred_type(media_types), expected)