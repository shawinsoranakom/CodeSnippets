def test_difference_with_values(self):
        ReservedName.objects.create(name="a", order=2)
        qs1 = ReservedName.objects.all()
        qs2 = ReservedName.objects.none()
        reserved_name = qs1.difference(qs2).values("name", "order", "id").get()
        self.assertEqual(reserved_name["name"], "a")
        self.assertEqual(reserved_name["order"], 2)
        reserved_name = qs1.difference(qs2).values_list("name", "order", "id").get()
        self.assertEqual(reserved_name[:2], ("a", 2))