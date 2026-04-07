def test_order_by_pk(self):
        """
        'pk' works as an ordering option in Meta.
        """
        self.assertEqual(
            [a.pk for a in Author.objects.all()],
            [a.pk for a in Author.objects.order_by("-pk")],
        )