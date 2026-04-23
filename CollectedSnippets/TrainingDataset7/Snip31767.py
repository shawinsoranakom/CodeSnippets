def test_one_to_one_as_pk(self):
        """
        If you use your own primary key field (such as a OneToOneField), it
        doesn't appear in the serialized field list - it replaces the pk
        identifier.
        """
        AuthorProfile.objects.create(
            author=self.joe, date_of_birth=datetime(1970, 1, 1)
        )
        serial_str = serializers.serialize(
            self.serializer_name, AuthorProfile.objects.all()
        )
        self.assertFalse(self._get_field_values(serial_str, "author"))

        for obj in serializers.deserialize(self.serializer_name, serial_str):
            self.assertEqual(obj.object.pk, self.joe.pk)