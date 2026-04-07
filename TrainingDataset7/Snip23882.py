def test_last(self):
        p1 = Person.objects.create(name="Alice", birthday=datetime(1950, 1, 1))
        p2 = Person.objects.create(name="Bob", birthday=datetime(1960, 2, 3))
        # Note: by default PK ordering.
        self.assertEqual(Person.objects.last(), p2)
        self.assertEqual(Person.objects.order_by("-name").last(), p1)
        self.assertEqual(
            Person.objects.filter(birthday__lte=datetime(1955, 1, 1)).last(), p1
        )
        self.assertIsNone(
            Person.objects.filter(birthday__lte=datetime(1940, 1, 1)).last()
        )