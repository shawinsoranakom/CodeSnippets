def test_queryset_update_on_parent_model(self):
        """
        Regression test for #10362
        It is possible to call update() and only change a field in
        an ancestor model.
        """
        article = ArticleWithAuthor.objects.create(
            author="fred",
            headline="Hey there!",
            pub_date=datetime.datetime(2009, 3, 1, 8, 0, 0),
        )
        update = ArticleWithAuthor.objects.filter(author="fred").update(
            headline="Oh, no!"
        )
        self.assertEqual(update, 1)
        update = ArticleWithAuthor.objects.filter(pk=article.pk).update(
            headline="Oh, no!"
        )
        self.assertEqual(update, 1)

        derivedm1 = DerivedM.objects.create(
            customPK=44,
            base_name="b1",
            derived_name="d1",
        )
        self.assertEqual(derivedm1.customPK, 44)
        self.assertEqual(derivedm1.base_name, "b1")
        self.assertEqual(derivedm1.derived_name, "d1")
        derivedms = list(DerivedM.objects.all())
        self.assertEqual(derivedms, [derivedm1])