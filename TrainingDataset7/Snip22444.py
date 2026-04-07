def test_translations(self):
        a1 = Article.objects.create(pub_date=datetime.date.today())
        at1_fi = ArticleTranslation(
            article=a1, lang="fi", title="Otsikko", body="Diipadaapa"
        )
        at1_fi.save()
        at2_en = ArticleTranslation(
            article=a1, lang="en", title="Title", body="Lalalalala"
        )
        at2_en.save()

        self.assertEqual(Article.objects.get(pk=a1.pk).active_translation, at1_fi)

        with self.assertNumQueries(1):
            fetched = Article.objects.select_related("active_translation").get(
                active_translation__title="Otsikko"
            )
            self.assertEqual(fetched.active_translation.title, "Otsikko")
        a2 = Article.objects.create(pub_date=datetime.date.today())
        at2_fi = ArticleTranslation(
            article=a2, lang="fi", title="Atsikko", body="Diipadaapa", abstract="dipad"
        )
        at2_fi.save()
        a3 = Article.objects.create(pub_date=datetime.date.today())
        at3_en = ArticleTranslation(
            article=a3, lang="en", title="A title", body="lalalalala", abstract="lala"
        )
        at3_en.save()
        # Test model initialization with active_translation field.
        a3 = Article(id=a3.id, pub_date=a3.pub_date, active_translation=at3_en)
        a3.save()
        self.assertEqual(
            list(Article.objects.filter(active_translation__abstract=None)), [a1, a3]
        )
        self.assertEqual(
            list(
                Article.objects.filter(
                    active_translation__abstract=None,
                    active_translation__pk__isnull=False,
                )
            ),
            [a1],
        )

        with translation.override("en"):
            self.assertEqual(
                list(Article.objects.filter(active_translation__abstract=None)),
                [a1, a2],
            )