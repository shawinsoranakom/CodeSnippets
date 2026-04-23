def test_get_transforms(self):
        @models.JSONField.register_lookup
        class MyTransform(Transform):
            lookup_name = "my_transform"

        field = models.JSONField()
        transform = field.get_transform("my_transform")
        self.assertIs(transform, MyTransform)
        models.JSONField._unregister_lookup(MyTransform)
        transform = field.get_transform("my_transform")
        self.assertIsInstance(transform, KeyTransformFactory)