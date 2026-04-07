def test_with_client(self):
        with self.assertNumQueries(1):
            self.client.get(self.url)

        with self.assertNumQueries(1):
            self.client.get(self.url)

        with self.assertNumQueries(2):
            self.client.get(self.url)
            self.client.get(self.url)