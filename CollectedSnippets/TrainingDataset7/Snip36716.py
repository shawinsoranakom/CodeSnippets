def test_depth_invalid(self):
        msg = "depth must be greater than 0."
        with self.assertRaisesMessage(ValueError, msg):
            timesince(self.t, self.t, depth=0)