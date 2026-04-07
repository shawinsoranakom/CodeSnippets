def test_select_related_defer(self):
        """
        #23370 - Should be able to defer child fields when using
        select_related() from parent to child.
        """
        qs = (
            Restaurant.objects.select_related("italianrestaurant")
            .defer("italianrestaurant__serves_gnocchi")
            .order_by("rating")
        )

        # The field was actually deferred
        with self.assertNumQueries(2):
            objs = list(qs.all())
            self.assertTrue(objs[1].italianrestaurant.serves_gnocchi)

        # Model fields where assigned correct values
        self.assertEqual(qs[0].name, "Demon Dogs")
        self.assertEqual(qs[0].rating, 2)
        self.assertEqual(qs[1].italianrestaurant.name, "Ristorante Miron")
        self.assertEqual(qs[1].italianrestaurant.rating, 4)