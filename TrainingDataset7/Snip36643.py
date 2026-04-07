def test_default_additional_attrs(self):
        s = SafeString("a&b")
        msg = "object has no attribute 'dynamic_attr'"
        with self.assertRaisesMessage(AttributeError, msg):
            s.dynamic_attr = True