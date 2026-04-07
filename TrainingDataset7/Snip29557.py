def test_other_array_types(self):
        instance = OtherTypesArrayModel(
            ips=["192.168.0.1", "::1"],
            uuids=[uuid.uuid4()],
            decimals=[decimal.Decimal(1.25), 1.75],
            tags=[Tag(1), Tag(2), Tag(3)],
            json=[{"a": 1}, {"b": 2}],
            int_ranges=[NumericRange(10, 20), NumericRange(30, 40)],
            bigint_ranges=[
                NumericRange(7000000000, 10000000000),
                NumericRange(50000000000, 70000000000),
            ],
        )
        instance.save()
        loaded = OtherTypesArrayModel.objects.get()
        self.assertEqual(instance.ips, loaded.ips)
        self.assertEqual(instance.uuids, loaded.uuids)
        self.assertEqual(instance.decimals, loaded.decimals)
        self.assertEqual(instance.tags, loaded.tags)
        self.assertEqual(instance.json, loaded.json)
        self.assertEqual(instance.int_ranges, loaded.int_ranges)
        self.assertEqual(instance.bigint_ranges, loaded.bigint_ranges)