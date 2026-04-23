def test_serialize(self):
        """Basic serialization works."""
        serial_str = serializers.serialize(self.serializer_name, Article.objects.all())
        self.assertTrue(self._validate_output(serial_str))