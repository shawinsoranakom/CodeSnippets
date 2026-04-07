def test_field_traversal(self):
        with self.assertNumQueries(1):
            s = (
                Species.objects.all()
                .select_related("genus__family__order")
                .order_by("id")[0:1]
                .get()
                .genus.family.order.name
            )
            self.assertEqual(s, "Diptera")