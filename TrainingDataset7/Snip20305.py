def test_dates_fails_when_given_invalid_order_argument(self):
        msg = "'order' must be either 'ASC' or 'DESC'."
        with self.assertRaisesMessage(ValueError, msg):
            Article.objects.dates("pub_date", "year", order="bad order")