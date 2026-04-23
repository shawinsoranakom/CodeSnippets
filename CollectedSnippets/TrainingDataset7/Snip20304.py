def test_dates_fails_when_given_invalid_kind_argument(self):
        msg = "'kind' must be one of 'year', 'month', 'week', or 'day'."
        with self.assertRaisesMessage(ValueError, msg):
            Article.objects.dates("pub_date", "bad_kind")