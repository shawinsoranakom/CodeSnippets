def test_update_binary(self):
        CaseTestModel.objects.update(
            binary=Case(
                When(integer=1, then=b"one"),
                When(integer=2, then=b"two"),
                default=b"",
            ),
        )
        self.assertQuerySetEqual(
            CaseTestModel.objects.order_by("pk"),
            [
                (1, b"one"),
                (2, b"two"),
                (3, b""),
                (2, b"two"),
                (3, b""),
                (3, b""),
                (4, b""),
            ],
            transform=lambda o: (o.integer, bytes(o.binary)),
        )