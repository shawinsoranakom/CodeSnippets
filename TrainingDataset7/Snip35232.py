def test_with_client_nested(self):
        with self.assertNumQueries(2):
            Person.objects.count()
            with self.assertNumQueries(0):
                pass
            self.client.get(self.url)