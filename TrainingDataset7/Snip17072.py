def assertObjectAttrs(self, obj, **kwargs):
        for attr, value in kwargs.items():
            self.assertEqual(getattr(obj, attr), value)