def test_manual_primary_key_test(self):
        """
        If you specify an existing primary key, but different other fields,
        then you will get an error and data will not be updated.
        """
        ManualPrimaryKeyTest.objects.create(id=1, data="Original")
        with self.assertRaises(IntegrityError):
            ManualPrimaryKeyTest.objects.update_or_create(id=1, data="Different")
        self.assertEqual(ManualPrimaryKeyTest.objects.get(id=1).data, "Original")