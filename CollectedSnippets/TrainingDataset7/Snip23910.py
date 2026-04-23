def test_create_with_duplicate_primary_key(self):
        """
        If you specify an existing primary key, but different other fields,
        then you will get an error and data will not be updated.
        """
        with self.assertRaises(IntegrityError):
            ManualPrimaryKeyTest.objects.get_or_create(id=1, data="Different")
        self.assertEqual(ManualPrimaryKeyTest.objects.get(id=1).data, "Original")