def test_timefield_changed(self):
        t1 = datetime.time(12, 51, 34, 482548)
        t2 = datetime.time(12, 51)
        f = TimeField(input_formats=["%H:%M", "%H:%M %p"])
        self.assertTrue(f.has_changed(t1, "12:51"))
        self.assertFalse(f.has_changed(t2, "12:51"))
        self.assertFalse(f.has_changed(t2, "12:51 PM"))