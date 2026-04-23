def test_values(self):
        self.assertUsesCursor(Person.objects.values("first_name").iterator())