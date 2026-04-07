def test_booleanfield_changed(self):
        f = BooleanField()
        self.assertFalse(f.has_changed(None, None))
        self.assertFalse(f.has_changed(None, ""))
        self.assertFalse(f.has_changed("", None))
        self.assertFalse(f.has_changed("", ""))
        self.assertTrue(f.has_changed(False, "on"))
        self.assertFalse(f.has_changed(True, "on"))
        self.assertTrue(f.has_changed(True, ""))
        # Initial value may have mutated to a string due to show_hidden_initial
        # (#19537)
        self.assertTrue(f.has_changed("False", "on"))
        # HiddenInput widget sends string values for boolean but doesn't clean
        # them in value_from_datadict.
        self.assertFalse(f.has_changed(False, "False"))
        self.assertFalse(f.has_changed(True, "True"))
        self.assertTrue(f.has_changed(False, "True"))
        self.assertTrue(f.has_changed(True, "False"))