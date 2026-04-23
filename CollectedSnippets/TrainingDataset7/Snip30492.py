def test_union_with_values(self):
        ReservedName.objects.create(name="a", order=2)
        qs1 = ReservedName.objects.all()
        reserved_name = qs1.union(qs1).values("name", "order", "id").get()
        self.assertEqual(reserved_name["name"], "a")
        self.assertEqual(reserved_name["order"], 2)
        reserved_name = qs1.union(qs1).values_list("name", "order", "id").get()
        self.assertEqual(reserved_name[:2], ("a", 2))
        # List of columns can be changed.
        reserved_name = qs1.union(qs1).values_list("order").get()
        self.assertEqual(reserved_name, (2,))