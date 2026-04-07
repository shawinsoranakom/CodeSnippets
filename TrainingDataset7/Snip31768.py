def test_serialize_field_subset(self):
        """Output can be restricted to a subset of fields"""
        valid_fields = ("headline", "pub_date")
        invalid_fields = ("author", "categories")
        serial_str = serializers.serialize(
            self.serializer_name, Article.objects.all(), fields=valid_fields
        )
        for field_name in invalid_fields:
            self.assertFalse(self._get_field_values(serial_str, field_name))

        for field_name in valid_fields:
            self.assertTrue(self._get_field_values(serial_str, field_name))