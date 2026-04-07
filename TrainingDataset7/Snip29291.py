def test_fetch_mode_fetch_peers_reverse(self):
        Restaurant.objects.create(
            place=self.p2, serves_hot_dogs=True, serves_pizza=False
        )
        p1, p2 = Place.objects.fetch_mode(FETCH_PEERS)
        with self.assertNumQueries(1):
            p1.restaurant
        with self.assertNumQueries(0):
            p2.restaurant