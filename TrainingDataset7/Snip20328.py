def test_cast_from_db_date_to_datetime(self):
        dt_value = datetime.date(2018, 9, 28)
        DTModel.objects.create(start_date=dt_value)
        dtm = DTModel.objects.annotate(
            start_as_datetime=Cast("start_date", models.DateTimeField())
        ).first()
        self.assertEqual(
            dtm.start_as_datetime, datetime.datetime(2018, 9, 28, 0, 0, 0, 0)
        )