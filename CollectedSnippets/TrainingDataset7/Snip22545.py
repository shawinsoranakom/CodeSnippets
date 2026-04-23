def test_overflow(self):
        msg = "The number of days must be between {min_days} and {max_days}.".format(
            min_days=datetime.timedelta.min.days,
            max_days=datetime.timedelta.max.days,
        )
        f = DurationField()
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("1000000000 00:00:00")
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("-1000000000 00:00:00")