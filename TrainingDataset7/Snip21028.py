def test_defer_fetch_mode_fetch_peers_single(self):
        p1 = Primary.objects.fetch_mode(FETCH_PEERS).defer("value").get(name="p1")
        with self.assertNumQueries(1):
            p1.value