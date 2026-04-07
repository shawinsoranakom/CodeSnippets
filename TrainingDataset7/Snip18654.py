def test_values_list_flat(self):
        self.assertUsesCursor(
            Person.objects.values_list("first_name", flat=True).iterator()
        )