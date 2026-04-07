def test_default_safe_data_additional_attrs(self):
        s = SafeData()
        msg = "object has no attribute 'dynamic_attr'"
        with self.assertRaisesMessage(AttributeError, msg):
            s.dynamic_attr = True