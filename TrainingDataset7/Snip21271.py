def test_garbage_collected_receiver(self):
        a = Callable()
        a_signal.connect(a.a, sender=self)
        del a
        garbage_collect()
        result = a_signal.send(sender=self, val="test")
        self.assertEqual(result, [])
        self.assertTestIsClean(a_signal)