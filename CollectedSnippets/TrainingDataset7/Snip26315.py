def test_related_manager_refresh(self):
        user_1 = User.objects.create(username="Jean")
        user_2 = User.objects.create(username="Joe")
        self.a3.authors.add(user_1.username)
        self.assertSequenceEqual(user_1.article_set.all(), [self.a3])
        # Change the username on a different instance of the same user.
        user_1_from_db = User.objects.get(pk=user_1.pk)
        self.assertSequenceEqual(user_1_from_db.article_set.all(), [self.a3])
        user_1_from_db.username = "Paul"
        self.a3.authors.set([user_2.username])
        user_1_from_db.save()
        # Assign a different article.
        self.a4.authors.add(user_1_from_db.username)
        self.assertSequenceEqual(user_1_from_db.article_set.all(), [self.a4])
        # Refresh the instance with an evaluated related manager.
        user_1.refresh_from_db()
        self.assertEqual(user_1.username, "Paul")
        self.assertSequenceEqual(user_1.article_set.all(), [self.a4])