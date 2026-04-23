def test_datetimes_fails_when_given_invalid_kind_argument(self):
        msg = (
            "'kind' must be one of 'year', 'month', 'week', 'day', 'hour', "
            "'minute', or 'second'."
        )
        with self.assertRaisesMessage(ValueError, msg):
            Article.objects.datetimes("pub_date", "bad_kind")