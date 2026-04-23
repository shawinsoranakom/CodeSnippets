def test_quality_over_specificity(self):
        """
        For media types with the same quality, prefer the more specific type.
        """
        request = HttpRequest()
        request.META["HTTP_ACCEPT"] = "text/*,image/jpeg"

        self.assertEqual(request.accepted_type("text/plain").quality, 1)
        self.assertEqual(request.accepted_type("text/plain").specificity, 1)

        self.assertEqual(request.accepted_type("image/jpeg").quality, 1)
        self.assertEqual(request.accepted_type("image/jpeg").specificity, 2)

        self.assertEqual(
            request.get_preferred_type(["text/plain", "image/jpeg"]), "image/jpeg"
        )