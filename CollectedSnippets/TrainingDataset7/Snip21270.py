def test_unweakrefable_sender(self):
        sender = object()
        a_signal.connect(receiver_1_arg, sender=sender)
        result = a_signal.send(sender=sender, val="test")
        self.assertEqual(result, [(receiver_1_arg, "test")])
        a_signal.disconnect(receiver_1_arg, sender=sender)
        self.assertTestIsClean(a_signal)