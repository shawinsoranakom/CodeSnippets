def test_create_models_m2m(self):
        """
        Models are created via the m2m relation if the remote model has a
        OneToOneField (#1064, #1506).
        """
        f = Favorites(name="Fred")
        f.save()
        f.restaurants.set([self.r1])
        self.assertSequenceEqual(f.restaurants.all(), [self.r1])