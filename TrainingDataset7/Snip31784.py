def test_serialize_inherited_fields(self):
        child_1 = Child.objects.create(parent_data="a", child_data="b")
        child_2 = Child.objects.create(parent_data="c", child_data="d")
        child_1.parent_m2m.add(child_2)
        child_data = serializers.serialize(self.serializer_name, [child_1, child_2])
        self.assertEqual(self._get_field_values(child_data, "parent_m2m"), [])
        self.assertEqual(self._get_field_values(child_data, "parent_data"), [])