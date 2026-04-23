def test_m2m_prefetch_reverse_proxied(self):
        result = Person.objects.filter(name="Dan").prefetch_related("special_event_set")
        with self.assertNumQueries(2):
            self.assertCountEqual(result, [self.dan])
            self.assertEqual(
                [event.name for event in result[0].special_event_set.all()],
                ["Exposition Match"],
            )