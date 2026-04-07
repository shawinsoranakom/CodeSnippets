def test_user_values_annotated_with_filtered_comments_id_count(self):
        self.assertSequenceEqual(
            User.objects.values("pk")
            .annotate(
                comments_count=Count(
                    "comments__id",
                    filter=Q(comments__text__icontains="foo"),
                )
            )
            .order_by("pk"),
            (
                {"pk": self.user_1.pk, "comments_count": 1},
                {"pk": self.user_2.pk, "comments_count": 1},
                {"pk": self.user_3.pk, "comments_count": 1},
            ),
        )