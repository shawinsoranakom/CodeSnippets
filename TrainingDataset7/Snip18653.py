def test_values_list(self):
        self.assertUsesCursor(Person.objects.values_list("first_name").iterator())