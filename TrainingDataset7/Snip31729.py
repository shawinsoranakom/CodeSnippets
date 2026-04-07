def forward_ref_m2m_with_error_test(self, format):
    t1 = NaturalKeyThing.objects.create(key="t1")
    t2 = NaturalKeyThing.objects.create(key="t2")
    t3 = NaturalKeyThing.objects.create(key="t3")
    t1.other_things.set([t2, t3])
    t1.save()
    string_data = serializers.serialize(
        format,
        [t1, t2],
        use_natural_primary_keys=True,
        use_natural_foreign_keys=True,
    )
    NaturalKeyThing.objects.all().delete()
    objs_with_deferred_fields = []
    for obj in serializers.deserialize(
        format, string_data, handle_forward_references=True
    ):
        obj.save()
        if obj.deferred_fields:
            objs_with_deferred_fields.append(obj)
    obj = objs_with_deferred_fields[0]
    msg = "NaturalKeyThing matching query does not exist"
    with self.assertRaisesMessage(serializers.base.DeserializationError, msg):
        obj.save_deferred_fields()