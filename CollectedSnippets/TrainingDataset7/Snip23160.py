def test_get_context_must_be_implemented(self):
        mixin = RenderableMixin()
        msg = "Subclasses of RenderableMixin must provide a get_context() method."
        with self.assertRaisesMessage(NotImplementedError, msg):
            mixin.get_context()