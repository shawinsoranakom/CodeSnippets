def test_users_annotated_with_comments_count(self):
        user_1, user_2, user_3 = User.objects.annotate(Count("comments")).order_by("pk")

        self.assertEqual(user_1, self.user_1)
        self.assertEqual(user_1.comments__count, 2)
        self.assertEqual(user_2, self.user_2)
        self.assertEqual(user_2.comments__count, 1)
        self.assertEqual(user_3, self.user_3)
        self.assertEqual(user_3.comments__count, 3)