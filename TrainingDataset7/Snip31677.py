def assert_serializer(self, format, data):
    # Create all the objects defined in the test data.
    objects = []
    for test_helper, pk, model, data_value in data:
        with connection.constraint_checks_disabled():
            objects.extend(test_helper.create_object(pk, model, data_value))

    # Get a count of the number of objects created for each model class.
    instance_counts = {}
    for _, _, model, _ in data:
        if model not in instance_counts:
            instance_counts[model] = model.objects.count()

    # Add the generic tagged objects to the object list.
    objects.extend(Tag.objects.all())

    # Serialize the test database.
    serialized_data = serializers.serialize(format, objects, indent=2)

    for obj in serializers.deserialize(format, serialized_data):
        obj.save()

    # Assert that the deserialized data is the same as the original source.
    for test_helper, pk, model, data_value in data:
        with self.subTest(model=model, data_value=data_value):
            test_helper.compare_object(self, pk, model, data_value)

    # Assert no new objects were created.
    for model, count in instance_counts.items():
        with self.subTest(model=model, count=count):
            self.assertEqual(count, model.objects.count())