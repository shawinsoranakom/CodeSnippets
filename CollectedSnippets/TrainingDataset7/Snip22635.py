def test_multiplechoicefield_changed(self):
        f = MultipleChoiceField(choices=[("1", "One"), ("2", "Two"), ("3", "Three")])
        self.assertFalse(f.has_changed(None, None))
        self.assertFalse(f.has_changed([], None))
        self.assertTrue(f.has_changed(None, ["1"]))
        self.assertFalse(f.has_changed([1, 2], ["1", "2"]))
        self.assertFalse(f.has_changed([2, 1], ["1", "2"]))
        self.assertTrue(f.has_changed([1, 2], ["1"]))
        self.assertTrue(f.has_changed([1, 2], ["1", "3"]))