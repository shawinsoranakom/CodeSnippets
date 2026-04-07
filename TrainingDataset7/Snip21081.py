def test_non_callable(self):
        msg = "on_delete must be callable."
        with self.assertRaisesMessage(TypeError, msg):
            models.ForeignKey("self", on_delete=None)
        with self.assertRaisesMessage(TypeError, msg):
            models.OneToOneField("self", on_delete=None)