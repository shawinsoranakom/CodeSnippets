def test_cannot_connect_non_callable(self):
        msg = "Signal receivers must be callable."
        with self.assertRaisesMessage(TypeError, msg):
            a_signal.connect(object())
        self.assertTestIsClean(a_signal)