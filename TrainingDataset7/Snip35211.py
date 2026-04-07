def test_empty(self):
        self.assertQuerySetEqual(Person.objects.filter(name="p3"), [])