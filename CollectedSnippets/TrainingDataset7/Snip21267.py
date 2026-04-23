def test_send_no_receivers(self):
        result = a_signal.send(sender=self, val="test")
        self.assertEqual(result, [])