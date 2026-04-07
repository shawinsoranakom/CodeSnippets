def test_does_not_exist(self):
        # Django raises an Article.DoesNotExist exception for get() if the
        # parameters don't match any object.
        with self.assertRaisesMessage(
            ObjectDoesNotExist, "Article matching query does not exist."
        ):
            Article.objects.get(
                id__exact=2000,
            )
        # To avoid dict-ordering related errors check only one lookup
        # in single assert.
        with self.assertRaises(ObjectDoesNotExist):
            Article.objects.get(pub_date__year=2005, pub_date__month=8)
        with self.assertRaisesMessage(
            ObjectDoesNotExist, "Article matching query does not exist."
        ):
            Article.objects.get(
                pub_date__week_day=6,
            )