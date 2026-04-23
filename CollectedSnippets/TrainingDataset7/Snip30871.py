def test_empty_string_promotion(self):
        qs = RelatedObject.objects.filter(single__name="")
        if connection.features.interprets_empty_strings_as_nulls:
            self.assertIn("LEFT OUTER JOIN", str(qs.query))
        else:
            self.assertNotIn("LEFT OUTER JOIN", str(qs.query))