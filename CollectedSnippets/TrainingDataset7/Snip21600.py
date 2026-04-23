def test_update_file(self):
        CaseTestModel.objects.update(
            file=Case(
                When(integer=1, then=Value("~/1")),
                When(integer=2, then=Value("~/2")),
            ),
        )
        self.assertQuerySetEqual(
            CaseTestModel.objects.order_by("pk"),
            [(1, "~/1"), (2, "~/2"), (3, ""), (2, "~/2"), (3, ""), (3, ""), (4, "")],
            transform=lambda o: (o.integer, str(o.file)),
        )