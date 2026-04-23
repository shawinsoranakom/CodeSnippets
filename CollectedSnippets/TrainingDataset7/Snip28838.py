def test_models_in_the_test_package(self):
        """
        Regression for #12245 - Models can exist in the test package, too.
        """
        p = Publication.objects.create(title="FooBar")
        ad = Advertisement.objects.create(customer="Lawrence Journal-World")
        ad.publications.add(p)

        ad = Advertisement.objects.get(id=ad.pk)
        self.assertEqual(ad.publications.count(), 1)