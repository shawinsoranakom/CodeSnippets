def test_receiver_signal_list(self):
        @receiver([a_signal, b_signal, c_signal])
        def f(val, **kwargs):
            self.state.append(val)

        self.state = []
        a_signal.send(sender=self, val="a")
        c_signal.send(sender=self, val="c")
        b_signal.send(sender=self, val="b")
        self.assertIn("a", self.state)
        self.assertIn("b", self.state)
        self.assertIn("c", self.state)