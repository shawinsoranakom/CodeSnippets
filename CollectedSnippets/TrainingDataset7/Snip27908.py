def test_unsaved_error(self):
        m = self.base_model(a=1, b=2)
        msg = "Cannot retrieve deferred field 'field' from an unsaved model."
        with self.assertRaisesMessage(AttributeError, msg):
            m.field