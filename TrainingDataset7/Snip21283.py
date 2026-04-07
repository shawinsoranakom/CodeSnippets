def test_receiver_single_signal(self):
        @receiver(a_signal)
        def f(val, **kwargs):
            self.state = val

        self.state = False
        a_signal.send(sender=self, val=True)
        self.assertTrue(self.state)