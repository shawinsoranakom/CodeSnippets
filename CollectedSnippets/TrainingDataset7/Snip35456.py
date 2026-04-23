def test_aware_time_unsupported(self):
        t = datetime.time(13, 20, 30, tzinfo=EAT)
        msg = "backend does not support timezone-aware times."
        with self.assertRaisesMessage(ValueError, msg):
            DailyEvent.objects.create(time=t)