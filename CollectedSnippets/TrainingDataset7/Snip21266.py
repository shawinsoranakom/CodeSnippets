def test_send(self):
        a_signal.connect(receiver_1_arg, sender=self)
        result = a_signal.send(sender=self, val="test")
        self.assertEqual(result, [(receiver_1_arg, "test")])
        a_signal.disconnect(receiver_1_arg, sender=self)
        self.assertTestIsClean(a_signal)