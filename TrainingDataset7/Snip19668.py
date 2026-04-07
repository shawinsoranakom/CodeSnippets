def test_order_comments_by_pk_expr(self):
        self.assertQuerySetEqual(
            Comment.objects.order_by("pk"),
            Comment.objects.order_by(F("pk")),
        )
        self.assertQuerySetEqual(
            Comment.objects.order_by("-pk"),
            Comment.objects.order_by(F("pk").desc()),
        )
        self.assertQuerySetEqual(
            Comment.objects.order_by("-pk"),
            Comment.objects.order_by(F("pk").desc(nulls_last=True)),
        )