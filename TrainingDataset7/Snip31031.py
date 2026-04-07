def test_quality_breaks_specificity(self):
        """
        With the same specificity, the quality breaks the tie.
        """
        request = HttpRequest()
        request.META["HTTP_ACCEPT"] = "text/plain;q=0.5,text/html"

        self.assertEqual(request.accepted_type("text/plain").quality, 0.5)
        self.assertEqual(request.accepted_type("text/plain").specificity, 2)

        self.assertEqual(request.accepted_type("text/html").quality, 1)
        self.assertEqual(request.accepted_type("text/html").specificity, 2)

        self.assertEqual(
            request.get_preferred_type(["text/html", "text/plain"]), "text/html"
        )