def test_adapt_timefield_value(self):
        msg = "Django does not support timezone-aware times."
        with self.assertRaisesMessage(ValueError, msg):
            self.ops.adapt_timefield_value(timezone.make_aware(timezone.now()))