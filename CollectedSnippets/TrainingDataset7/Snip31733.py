def nullable_natural_key_fk_test(self, format):
    target_with_none = NaturalKeyWithNullableField.objects.create(
        name="test_none",
        optional_id=None,
    )
    target_with_value = NaturalKeyWithNullableField.objects.create(
        name="test_value",
        optional_id="some_id",
    )
    fk_to_none = FKToNaturalKeyWithNullable.objects.create(
        ref=target_with_none,
        data="points_to_none",
    )
    fk_to_value = FKToNaturalKeyWithNullable.objects.create(
        ref=target_with_value,
        data="points_to_value",
    )
    objects = [target_with_none, target_with_value, fk_to_none, fk_to_value]
    serialized = serializers.serialize(
        format,
        objects,
        use_natural_foreign_keys=True,
        use_natural_primary_keys=True,
    )
    objs = list(serializers.deserialize(format, serialized))
    self.assertEqual(objs[2].object.ref_id, target_with_none.pk)
    self.assertEqual(objs[3].object.ref_id, target_with_value.pk)