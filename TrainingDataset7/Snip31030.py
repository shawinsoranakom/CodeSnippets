def test_quality_for_media_type_rfc9110(self):
        """
        Taken from
        https://www.rfc-editor.org/rfc/rfc9110.html#section-12.5.1-18.
        """
        request = HttpRequest()
        request.META["HTTP_ACCEPT"] = (
            "text/*;q=0.3, text/plain;q=0.7, text/plain;format=flowed, "
            "text/plain;format=fixed;q=0.4, */*;q=0.5"
        )

        for media_type, quality in [
            ("text/plain;format=flowed", 1),
            ("text/plain", 0.7),
            ("text/html", 0.3),
            ("image/jpeg", 0.5),
            ("text/plain;format=fixed", 0.4),
            ("text/html;level=3", 0.3),  # https://www.rfc-editor.org/errata/eid7138
        ]:
            with self.subTest(media_type):
                accepted_media_type = request.accepted_type(media_type)
                self.assertIsNotNone(accepted_media_type)
                self.assertEqual(accepted_media_type.quality, quality)

        for media_types, expected in [
            (["text/plain", "text/plain; format=flowed"], "text/plain; format=flowed"),
            (["text/html", "image/jpeg"], "image/jpeg"),
        ]:
            self.assertEqual(request.get_preferred_type(media_types), expected)