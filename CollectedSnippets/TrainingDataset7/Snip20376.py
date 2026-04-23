def test_extract_lookup_name_sql_injection(self):
        start_datetime = datetime.datetime(2015, 6, 15, 14, 30, 50, 321)
        end_datetime = datetime.datetime(2016, 6, 15, 14, 10, 50, 123)
        if settings.USE_TZ:
            start_datetime = timezone.make_aware(start_datetime)
            end_datetime = timezone.make_aware(end_datetime)
        self.create_model(start_datetime, end_datetime)
        self.create_model(end_datetime, start_datetime)

        with self.assertRaises((OperationalError, ValueError)):
            DTModel.objects.filter(
                start_datetime__year=Extract(
                    "start_datetime", "day' FROM start_datetime)) OR 1=1;--"
                )
            ).exists()