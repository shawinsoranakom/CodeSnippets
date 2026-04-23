def test_update_generic_ip_address(self):
        CaseTestModel.objects.update(
            generic_ip_address=Case(
                When(integer=1, then=Value("1.1.1.1")),
                When(integer=2, then=Value("2.2.2.2")),
                output_field=GenericIPAddressField(),
            ),
        )
        self.assertQuerySetEqual(
            CaseTestModel.objects.order_by("pk"),
            [
                (1, "1.1.1.1"),
                (2, "2.2.2.2"),
                (3, None),
                (2, "2.2.2.2"),
                (3, None),
                (3, None),
                (4, None),
            ],
            transform=attrgetter("integer", "generic_ip_address"),
        )