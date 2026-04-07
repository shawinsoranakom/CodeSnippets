def test_query_convert_timezones(self):
        # Connection timezone is equal to the current timezone, datetime
        # shouldn't be converted.
        with override_database_connection_timezone("Africa/Nairobi"):
            event_datetime = datetime.datetime(2016, 1, 2, 23, 10, 11, 123, tzinfo=EAT)
            event = Event.objects.create(dt=event_datetime)
            self.assertEqual(
                Event.objects.filter(dt__date=event_datetime.date()).first(), event
            )
        # Connection timezone is not equal to the current timezone, datetime
        # should be converted (-4h).
        with override_database_connection_timezone("Asia/Bangkok"):
            event_datetime = datetime.datetime(2016, 1, 2, 3, 10, 11, tzinfo=ICT)
            event = Event.objects.create(dt=event_datetime)
            self.assertEqual(
                Event.objects.filter(dt__date=datetime.date(2016, 1, 1)).first(), event
            )