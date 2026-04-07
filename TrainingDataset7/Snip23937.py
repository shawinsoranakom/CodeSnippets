def test_create_with_duplicate_primary_key(self):
        """
        If an existing primary key is specified with different values for other
        fields, then IntegrityError is raised and data isn't updated.
        """
        ManualPrimaryKeyTest.objects.create(id=1, data="Original")
        with self.assertRaises(IntegrityError):
            ManualPrimaryKeyTest.objects.update_or_create(id=1, data="Different")
        self.assertEqual(ManualPrimaryKeyTest.objects.get(id=1).data, "Original")