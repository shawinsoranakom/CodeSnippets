def pk_with_default(self, format):
    """
    The deserializer works with natural keys when the primary key has a default
    value.
    """
    obj = NaturalPKWithDefault.objects.create(name="name")
    string_data = serializers.serialize(
        format,
        NaturalPKWithDefault.objects.all(),
        use_natural_foreign_keys=True,
        use_natural_primary_keys=True,
    )
    objs = list(serializers.deserialize(format, string_data))
    self.assertEqual(len(objs), 1)
    self.assertEqual(objs[0].object.pk, obj.pk)