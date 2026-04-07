def test_field_mixin_as_widget_must_be_implemented(self):
        mixin = RenderableFieldMixin()
        msg = "Subclasses of RenderableFieldMixin must provide an as_widget() method."
        with self.assertRaisesMessage(NotImplementedError, msg):
            mixin.as_widget()