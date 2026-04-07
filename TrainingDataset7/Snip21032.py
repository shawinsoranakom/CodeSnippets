def test_defer_fetch_mode_fetch_peers(self):
        p1, p2 = Primary.objects.using("other").fetch_mode(FETCH_PEERS).defer("value")
        with self.assertNumQueries(1, using="other"):
            p1.value
        with self.assertNumQueries(0, using="other"):
            p2.value