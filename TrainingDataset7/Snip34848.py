def listener(*args, **kwargs):
            listener.executed = True
            self.assertEqual(kwargs["sender"], User)