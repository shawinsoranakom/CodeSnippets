def test_self_referential_one_to_one(self):
        first = Item.objects.create(name="first", value=1)
        second = Item.objects.create(name="second", value=2, source=first)
        with self.assertNumQueries(1):
            deferred_first, deferred_second = (
                Item.objects.select_related("source", "destination")
                .only("name", "source__name", "destination__value")
                .order_by("pk")
            )
        with self.assertNumQueries(0):
            self.assertEqual(deferred_first.name, first.name)
            self.assertEqual(deferred_second.name, second.name)
            self.assertEqual(deferred_second.source.name, first.name)
            self.assertEqual(deferred_first.destination.value, second.value)
        with self.assertNumQueries(1):
            self.assertEqual(deferred_first.value, first.value)
        with self.assertNumQueries(1):
            self.assertEqual(deferred_second.source.value, first.value)
        with self.assertNumQueries(1):
            self.assertEqual(deferred_first.destination.name, second.name)