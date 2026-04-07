def test_can_mix_and_match_position_and_kwargs(self):
        # You can also mix and match position and keyword arguments, but
        # be sure not to duplicate field information.
        a = Article(None, "Fourth article", pub_date=datetime(2005, 7, 31))
        a.save()
        self.assertEqual(a.headline, "Fourth article")