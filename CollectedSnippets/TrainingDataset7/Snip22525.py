def test_datetimefield_clean_invalid(self):
        f = DateTimeField()
        msg = "'Enter a valid date/time.'"
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("hello")
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("2006-10-25 4:30 p.m.")
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("   ")
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("2014-09-23T28:23")
        f = DateTimeField(input_formats=["%Y %m %d %I:%M %p"])
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("2006.10.25 14:30:45")