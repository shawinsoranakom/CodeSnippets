def test_settings_delete_wrapped(self):
        with self.assertRaisesMessage(TypeError, "can't delete _wrapped."):
            delattr(settings, "_wrapped")