def test_foreignkey(self):
        with self.assertNumQueries(2):
            qs = Author.objects.prefetch_related("addresses")
            addresses = [
                [str(address) for address in obj.addresses.all()] for obj in qs
            ]
        self.assertEqual(addresses, [[str(self.author_address)], [], []])