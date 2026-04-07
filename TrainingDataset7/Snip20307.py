def test_dates_avoid_datetime_cast(self):
        Article.objects.create(pub_date=datetime.date(2015, 10, 21))
        for kind in ["day", "month", "year"]:
            qs = Article.objects.dates("pub_date", kind)
            if kind == "day":
                self.assertIn("DATE(", str(qs.query))
            else:
                self.assertIn(" AS DATE)", str(qs.query))