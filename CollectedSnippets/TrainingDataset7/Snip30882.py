def test_ticket_14056(self):
        s1 = SharedConnection.objects.create(data="s1")
        s2 = SharedConnection.objects.create(data="s2")
        s3 = SharedConnection.objects.create(data="s3")
        PointerA.objects.create(connection=s2)
        expected_ordering = (
            [s1, s3, s2] if connection.features.nulls_order_largest else [s2, s1, s3]
        )
        self.assertSequenceEqual(
            SharedConnection.objects.order_by("-pointera__connection", "pk"),
            expected_ordering,
        )