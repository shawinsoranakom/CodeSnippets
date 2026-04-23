def test_update_file_path(self):
        CaseTestModel.objects.update(
            file_path=Case(
                When(integer=1, then=Value("~/1")),
                When(integer=2, then=Value("~/2")),
                default=Value(""),
            ),
        )
        self.assertQuerySetEqual(
            CaseTestModel.objects.order_by("pk"),
            [(1, "~/1"), (2, "~/2"), (3, ""), (2, "~/2"), (3, ""), (3, ""), (4, "")],
            transform=attrgetter("integer", "file_path"),
        )