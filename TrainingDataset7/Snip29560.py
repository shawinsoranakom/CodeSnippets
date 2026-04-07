def test_nested_nullable_base_field(self):
        instance = NullableIntegerArrayModel.objects.create(
            field_nested=[[None, None], [None, None]],
        )
        self.assertEqual(instance.field_nested, [[None, None], [None, None]])