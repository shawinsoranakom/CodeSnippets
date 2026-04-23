def natural_key_serializer_test(self, format):
    # Create all the objects defined in the test data
    with connection.constraint_checks_disabled():
        objects = [
            NaturalKeyAnchor.objects.create(id=1100, data="Natural Key Anghor"),
            FKDataNaturalKey.objects.create(id=1101, data_id=1100),
            FKDataNaturalKey.objects.create(id=1102, data_id=None),
        ]
    # Serialize the test database
    serialized_data = serializers.serialize(
        format, objects, indent=2, use_natural_foreign_keys=True
    )

    for obj in serializers.deserialize(format, serialized_data):
        obj.save()

    # Assert that the deserialized data is the same
    # as the original source
    for obj in objects:
        instance = obj.__class__.objects.get(id=obj.pk)
        self.assertEqual(
            obj.data,
            instance.data,
            "Objects with PK=%s not equal; expected '%s' (%s), got '%s' (%s)"
            % (
                obj.pk,
                obj.data,
                type(obj.data),
                instance,
                type(instance.data),
            ),
        )