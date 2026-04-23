def nullable_natural_key_m2m_test(self, format):
    target_with_none = NaturalKeyWithNullableField.objects.create(
        name="test_none",
        optional_id=None,
    )
    target_with_value = NaturalKeyWithNullableField.objects.create(
        name="test_value",
        optional_id="some_id",
    )
    m2m_obj = FKToNaturalKeyWithNullable.objects.create(data="m2m_test")
    m2m_obj.refs.set([target_with_none, target_with_value])
    objects = [target_with_none, target_with_value, m2m_obj]
    serialized = serializers.serialize(
        format,
        objects,
        use_natural_foreign_keys=True,
        use_natural_primary_keys=True,
    )
    objs = list(serializers.deserialize(format, serialized))
    self.assertCountEqual(
        objs[2].m2m_data["refs"],
        [target_with_none.pk, target_with_value.pk],
    )