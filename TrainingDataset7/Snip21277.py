def test_send_robust_no_receivers(self):
        result = a_signal.send_robust(sender=self, val="test")
        self.assertEqual(result, [])