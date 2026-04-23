def test_specialized_queryset(self):
        self.assert_pickles(Happening.objects.values("name"))
        self.assert_pickles(Happening.objects.values("name").dates("when", "year"))
        # With related field (#14515)
        self.assert_pickles(
            Event.objects.select_related("group")
            .order_by("title")
            .values_list("title", "group__name")
        )