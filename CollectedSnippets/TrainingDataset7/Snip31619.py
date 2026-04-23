def test_null_join_promotion(self):
        australia = Country.objects.create(name="Australia")
        active = ClientStatus.objects.create(name="active")

        wa = State.objects.create(name="Western Australia", country=australia)
        bob = Client.objects.create(name="Bob", status=active)
        jack = Client.objects.create(name="Jack", status=active, state=wa)
        qs = Client.objects.filter(state=wa).select_related("state")
        with self.assertNumQueries(1):
            self.assertEqual(list(qs), [jack])
            self.assertEqual(qs[0].state, wa)
            # The select_related join wasn't promoted as there was already an
            # existing (even if trimmed) inner join to state.
            self.assertNotIn("LEFT OUTER", str(qs.query))
        qs = Client.objects.select_related("state").order_by("name")
        with self.assertNumQueries(1):
            self.assertEqual(list(qs), [bob, jack])
            self.assertIs(qs[0].state, None)
            self.assertEqual(qs[1].state, wa)
            # The select_related join was promoted as there is already an
            # existing join.
            self.assertIn("LEFT OUTER", str(qs.query))