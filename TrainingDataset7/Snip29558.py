def test_null_from_db_value_handling(self):
        instance = OtherTypesArrayModel.objects.create(
            ips=["192.168.0.1", "::1"],
            uuids=[uuid.uuid4()],
            decimals=[decimal.Decimal(1.25), 1.75],
            tags=None,
        )
        instance.refresh_from_db()
        self.assertIsNone(instance.tags)
        self.assertEqual(instance.json, [])
        self.assertIsNone(instance.int_ranges)
        self.assertIsNone(instance.bigint_ranges)