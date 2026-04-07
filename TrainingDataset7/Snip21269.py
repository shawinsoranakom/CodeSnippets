def test_send_different_no_sender(self):
        a_signal.connect(receiver_1_arg, sender=object)
        result = a_signal.send(sender=self, val="test")
        self.assertEqual(result, [])
        a_signal.disconnect(receiver_1_arg, sender=object)
        self.assertTestIsClean(a_signal)