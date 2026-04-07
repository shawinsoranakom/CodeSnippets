def test_cast_from_python_to_date(self):
        today = datetime.date.today()
        dates = Author.objects.annotate(cast_date=Cast(today, models.DateField()))
        self.assertEqual(dates.get().cast_date, today)