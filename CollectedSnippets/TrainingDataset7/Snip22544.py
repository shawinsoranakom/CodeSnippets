def test_durationfield_clean_not_required(self):
        f = DurationField(required=False)
        self.assertIsNone(f.clean(""))