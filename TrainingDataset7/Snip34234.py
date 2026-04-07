def verify_tag(self, tag, name):
        self.assertEqual(tag.__name__, name)
        self.assertEqual(tag.__doc__, "Expected %s __doc__" % name)
        self.assertEqual(tag.__dict__["anything"], "Expected %s __dict__" % name)