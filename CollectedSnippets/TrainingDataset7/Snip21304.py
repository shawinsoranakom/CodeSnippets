def test_distinct_on_get_ordering_preserved(self):
        """
        Ordering shouldn't be cleared when distinct on fields are specified.
        refs #25081
        """
        staff = (
            Staff.objects.distinct("name")
            .order_by("name", "-organisation")
            .get(name="p1")
        )
        self.assertEqual(staff.organisation, "o2")