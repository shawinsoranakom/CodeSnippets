def test_durationfield_clean(self):
        f = DurationField()
        self.assertEqual(datetime.timedelta(seconds=30), f.clean("30"))
        self.assertEqual(datetime.timedelta(minutes=15, seconds=30), f.clean("15:30"))
        self.assertEqual(
            datetime.timedelta(hours=1, minutes=15, seconds=30), f.clean("1:15:30")
        )
        self.assertEqual(
            datetime.timedelta(
                days=1, hours=1, minutes=15, seconds=30, milliseconds=300
            ),
            f.clean("1 1:15:30.3"),
        )
        self.assertEqual(
            datetime.timedelta(0, 10800),
            f.clean(datetime.timedelta(0, 10800)),
        )
        msg = "This field is required."
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("")
        msg = "Enter a valid duration."
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("not_a_time")
        with self.assertRaisesMessage(ValidationError, msg):
            DurationField().clean("P3(3D")