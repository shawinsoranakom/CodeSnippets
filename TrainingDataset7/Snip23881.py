def test_first(self):
        p1 = Person.objects.create(name="Bob", birthday=datetime(1950, 1, 1))
        p2 = Person.objects.create(name="Alice", birthday=datetime(1961, 2, 3))
        self.assertEqual(Person.objects.first(), p1)
        self.assertEqual(Person.objects.order_by("name").first(), p2)
        self.assertEqual(
            Person.objects.filter(birthday__lte=datetime(1955, 1, 1)).first(), p1
        )
        self.assertIsNone(
            Person.objects.filter(birthday__lte=datetime(1940, 1, 1)).first()
        )