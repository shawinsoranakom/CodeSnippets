def __set_name__(self_, owner, name):
                self.assertIsNone(self_.called)
                self_.called = (owner, name)