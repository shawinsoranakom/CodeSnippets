def test_lookup_date_as_str(self):
        # A date lookup can be performed using a string search
        self.assertSequenceEqual(
            Article.objects.filter(pub_date__startswith="2005"),
            [self.a5, self.a6, self.a4, self.a2, self.a3, self.a7, self.a1],
        )