def test_deserialize_force_insert(self):
        """
        Deserialized content can be saved with force_insert as a parameter.
        """
        serial_str = serializers.serialize(self.serializer_name, [self.a1])
        deserial_obj = list(serializers.deserialize(self.serializer_name, serial_str))[
            0
        ]
        with mock.patch("django.db.models.Model") as mock_model:
            deserial_obj.save(force_insert=False)
            mock_model.save_base.assert_called_with(
                deserial_obj.object, raw=True, using=None, force_insert=False
            )