def test_field_mixin_as_hidden_must_be_implemented(self):
        mixin = RenderableFieldMixin()
        msg = "Subclasses of RenderableFieldMixin must provide an as_hidden() method."
        with self.assertRaisesMessage(NotImplementedError, msg):
            mixin.as_hidden()