def test_m2m_prefetch_proxied(self):
        result = Event.objects.filter(name="Exposition Match").prefetch_related(
            "special_people"
        )
        with self.assertNumQueries(2):
            self.assertCountEqual(result, [self.event])
            self.assertEqual(
                sorted(p.name for p in result[0].special_people.all()), ["Chris", "Dan"]
            )