def test_cast_from_db_datetime_to_time(self):
        dt_value = datetime.datetime(2018, 9, 28, 12, 42, 10, 234567)
        DTModel.objects.create(start_datetime=dt_value)
        dtm = DTModel.objects.annotate(
            start_datetime_as_time=Cast("start_datetime", models.TimeField())
        ).first()
        rounded_ms = int(
            round(0.234567, connection.features.time_cast_precision) * 10**6
        )
        self.assertEqual(
            dtm.start_datetime_as_time, datetime.time(12, 42, 10, rounded_ms)
        )