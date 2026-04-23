def test_reverse_object_does_not_exist_cache(self):
        """
        Regression for #13839 and #17439.

        DoesNotExist on a reverse one-to-one relation is cached.
        """
        p = Place(name="Zombie Cats", address="Not sure")
        p.save()
        with self.assertNumQueries(1):
            with self.assertRaises(Restaurant.DoesNotExist):
                p.restaurant
        with self.assertNumQueries(0):
            with self.assertRaises(Restaurant.DoesNotExist):
                p.restaurant