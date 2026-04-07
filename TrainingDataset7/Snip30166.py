def test_reverse_one_to_one_then_m2m(self):
        """
        A m2m relation can be followed after going through the select_related
        reverse of an o2o.
        """
        qs = Author.objects.prefetch_related("bio__books").select_related("bio")

        with self.assertNumQueries(1):
            list(qs.all())

        Bio.objects.create(author=self.author1)
        with self.assertNumQueries(2):
            list(qs.all())