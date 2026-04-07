def test_cast_from_db_datetime_to_date(self):
        dt_value = datetime.datetime(2018, 9, 28, 12, 42, 10, 234567)
        DTModel.objects.create(start_datetime=dt_value)
        dtm = DTModel.objects.annotate(
            start_datetime_as_date=Cast("start_datetime", models.DateField())
        ).first()
        self.assertEqual(dtm.start_datetime_as_date, datetime.date(2018, 9, 28))