def test_datetimefield_changed(self):
        f = DateTimeField(input_formats=["%Y %m %d %I:%M %p"])
        d = datetime(2006, 9, 17, 14, 30, 0)
        self.assertFalse(f.has_changed(d, "2006 09 17 2:30 PM"))