def test_too_many(self):
        # Create a very similar object
        a = Article(
            id=None,
            headline="Swallow bites Python",
            pub_date=datetime(2005, 7, 28),
        )
        a.save()

        self.assertEqual(Article.objects.count(), 2)

        # Django raises an Article.MultipleObjectsReturned exception if the
        # lookup matches more than one object
        msg = "get() returned more than one Article -- it returned 2!"
        with self.assertRaisesMessage(MultipleObjectsReturned, msg):
            Article.objects.get(
                headline__startswith="Swallow",
            )
        with self.assertRaisesMessage(MultipleObjectsReturned, msg):
            Article.objects.get(
                pub_date__year=2005,
            )
        with self.assertRaisesMessage(MultipleObjectsReturned, msg):
            Article.objects.get(pub_date__year=2005, pub_date__month=7)