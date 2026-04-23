def test_deferred_field_serialization(self):
        author = Author.objects.create(name="Victor Hugo")
        author = Author.objects.defer("name").get(pk=author.pk)
        serial_str = serializers.serialize(self.serializer_name, [author])
        deserial_objs = list(serializers.deserialize(self.serializer_name, serial_str))
        self.assertIsInstance(deserial_objs[0].object, Author)