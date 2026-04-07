def natural_key_m2m_totally_ordered_test(self, format):
    t1 = NaturalKeyThing.objects.create(key="t1")
    t2 = NaturalKeyThing.objects.create(key="t2")
    t3 = NaturalKeyThing.objects.create(key="t3")
    t1.other_things.add(t2, t3)

    with mock.patch.object(models.QuerySet, "order_by") as mock_order_by:
        serializers.serialize(format, [t1], use_natural_foreign_keys=True)
        mock_order_by.assert_called_once_with("pk")
        mock_order_by.reset_mock()
        serializers.serialize(format, [t1], use_natural_foreign_keys=False)
        mock_order_by.assert_called_once_with("pk")