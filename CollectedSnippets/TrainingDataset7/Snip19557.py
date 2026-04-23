def test_user_values_annotated_with_comments_id_count(self):
        self.assertSequenceEqual(
            User.objects.values("pk").annotate(Count("comments__id")).order_by("pk"),
            (
                {"pk": self.user_1.pk, "comments__id__count": 2},
                {"pk": self.user_2.pk, "comments__id__count": 1},
                {"pk": self.user_3.pk, "comments__id__count": 3},
            ),
        )