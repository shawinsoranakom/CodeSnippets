def test_only_fetch_mode_fetch_peers(self):
        p1, p2 = Primary.objects.fetch_mode(FETCH_PEERS).only("name")
        with self.assertNumQueries(1):
            p1.value
        with self.assertNumQueries(0):
            p2.value