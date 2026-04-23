def listener(*args, **kwargs):
            self.assertEqual(kwargs["sender"], CustomUser)
            listener.executed = True