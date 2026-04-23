def test_update_url(self):
        CaseTestModel.objects.update(
            url=Case(
                When(integer=1, then=Value("http://1.example.com/")),
                When(integer=2, then=Value("http://2.example.com/")),
                default=Value(""),
            ),
        )
        self.assertQuerySetEqual(
            CaseTestModel.objects.order_by("pk"),
            [
                (1, "http://1.example.com/"),
                (2, "http://2.example.com/"),
                (3, ""),
                (2, "http://2.example.com/"),
                (3, ""),
                (3, ""),
                (4, ""),
            ],
            transform=attrgetter("integer", "url"),
        )