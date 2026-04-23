def test_fetch_mode_fetch_peers_forward(self):
        Restaurant.objects.create(
            place=self.p2, serves_hot_dogs=True, serves_pizza=False
        )
        r1, r2 = Restaurant.objects.fetch_mode(FETCH_PEERS)
        with self.assertNumQueries(1):
            r1.place
        with self.assertNumQueries(0):
            r2.place