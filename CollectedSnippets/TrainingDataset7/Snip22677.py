def test_splitdatetimefield_changed(self):
        f = SplitDateTimeField(input_date_formats=["%d/%m/%Y"])
        self.assertFalse(
            f.has_changed(["11/01/2012", "09:18:15"], ["11/01/2012", "09:18:15"])
        )
        self.assertTrue(
            f.has_changed(
                datetime.datetime(2008, 5, 6, 12, 40, 00), ["2008-05-06", "12:40:00"]
            )
        )
        self.assertFalse(
            f.has_changed(
                datetime.datetime(2008, 5, 6, 12, 40, 00), ["06/05/2008", "12:40"]
            )
        )
        self.assertTrue(
            f.has_changed(
                datetime.datetime(2008, 5, 6, 12, 40, 00), ["06/05/2008", "12:41"]
            )
        )