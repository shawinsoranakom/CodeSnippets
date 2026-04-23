def test_garbage_collected_sender(self):
        signal = Signal()

        class Sender:
            pass

        def make_id(target):
            """
            Simulate id() reuse for distinct senders with non-overlapping
            lifetimes that would require memory contention to reproduce.
            """
            if isinstance(target, Sender):
                return 0
            return _make_id(target)

        def first_receiver(attempt, **kwargs):
            return attempt

        def second_receiver(attempt, **kwargs):
            return attempt

        with mock.patch("django.dispatch.dispatcher._make_id", make_id):
            sender = Sender()
            signal.connect(first_receiver, sender)
            result = signal.send(sender, attempt="first")
            self.assertEqual(result, [(first_receiver, "first")])

            del sender
            garbage_collect()

            sender = Sender()
            signal.connect(second_receiver, sender)
            result = signal.send(sender, attempt="second")
            self.assertEqual(result, [(second_receiver, "second")])