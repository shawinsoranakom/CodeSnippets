def test_get_next_prev_by_field(self):
        # get_next_by_FIELD() and get_previous_by_FIELD() don't crash when
        # microseconds values are stored in the database.
        Event.objects.create(when=datetime.datetime(2000, 1, 1, 16, 0, 0))
        Event.objects.create(when=datetime.datetime(2000, 1, 1, 6, 1, 1))
        Event.objects.create(when=datetime.datetime(2000, 1, 1, 13, 1, 1))
        e = Event.objects.create(when=datetime.datetime(2000, 1, 1, 12, 0, 20, 24))
        self.assertEqual(
            e.get_next_by_when().when, datetime.datetime(2000, 1, 1, 13, 1, 1)
        )
        self.assertEqual(
            e.get_previous_by_when().when, datetime.datetime(2000, 1, 1, 6, 1, 1)
        )