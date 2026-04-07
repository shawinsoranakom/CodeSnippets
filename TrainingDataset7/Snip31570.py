def test_list_with_depth(self):
        """
        Passing a relationship field lookup specifier to select_related() will
        stop the descent at a particular level. This can be used on lists as
        well.
        """
        with self.assertNumQueries(5):
            world = Species.objects.select_related("genus__family")
            orders = [o.genus.family.order.name for o in world]
            self.assertEqual(
                sorted(orders), ["Agaricales", "Diptera", "Fabales", "Primates"]
            )