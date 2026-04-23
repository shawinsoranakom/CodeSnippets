def test_queryset_class_getitem(self):
        self.assertIs(models.QuerySet[Post], models.QuerySet)
        self.assertIs(models.QuerySet[Post, Post], models.QuerySet)
        self.assertIs(models.QuerySet[Post, int, str], models.QuerySet)