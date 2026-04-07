def test_update_string(self):
        CaseTestModel.objects.filter(string__in=["1", "2"]).update(
            string=Case(
                When(integer=1, then=Value("1")),
                When(integer=2, then=Value("2")),
            ),
        )
        self.assertQuerySetEqual(
            CaseTestModel.objects.filter(string__in=["1", "2"]).order_by("pk"),
            [(1, "1"), (2, "2"), (2, "2")],
            transform=attrgetter("integer", "string"),
        )