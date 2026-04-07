def test_key_transform_text_lookup_mixin_non_key_transform(self):
        transform = Transform("test")
        msg = (
            "Transform should be an instance of KeyTransform in order to use "
            "this lookup."
        )
        with self.assertRaisesMessage(TypeError, msg):
            KeyTransformTextLookupMixin(transform)