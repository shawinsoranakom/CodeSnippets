def test_send_robust_success(self):
        a_signal.connect(receiver_1_arg)
        result = a_signal.send_robust(sender=self, val="test")
        self.assertEqual(result, [(receiver_1_arg, "test")])
        a_signal.disconnect(receiver_1_arg)
        self.assertTestIsClean(a_signal)