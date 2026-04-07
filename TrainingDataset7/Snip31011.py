def test_str(self):
        self.assertEqual(str(MediaType("*/*; q=0.8")), "*/*; q=0.8")
        self.assertEqual(str(MediaType("application/xml")), "application/xml")
        self.assertEqual(
            str(MediaType("application/xml;type=madeup;q=42")),
            "application/xml; type=madeup; q=42",
        )