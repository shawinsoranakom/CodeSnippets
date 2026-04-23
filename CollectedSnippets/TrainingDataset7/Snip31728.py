def forward_ref_m2m_test(self, format):
    t1 = NaturalKeyThing.objects.create(key="t1")
    t2 = NaturalKeyThing.objects.create(key="t2")
    t3 = NaturalKeyThing.objects.create(key="t3")
    t1.other_things.set([t2, t3])
    string_data = serializers.serialize(
        format,
        [t1, t2, t3],
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
    for obj in objs_with_deferred_fields:
        obj.save_deferred_fields()
    t1 = NaturalKeyThing.objects.get(key="t1")
    t2 = NaturalKeyThing.objects.get(key="t2")
    t3 = NaturalKeyThing.objects.get(key="t3")
    self.assertCountEqual(t1.other_things.all(), [t2, t3])