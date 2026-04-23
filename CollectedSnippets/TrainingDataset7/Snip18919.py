def test_emptyqs_customqs(self):
        # A hacky test for custom QuerySet subclass - refs #17271
        Article.objects.create(headline="foo", pub_date=datetime.now())

        class CustomQuerySet(models.QuerySet):
            def do_something(self):
                return "did something"

        qs = Article.objects.all()
        qs.__class__ = CustomQuerySet
        qs = qs.none()
        with self.assertNumQueries(0):
            self.assertEqual(len(qs), 0)
            self.assertIsInstance(qs, EmptyQuerySet)
            self.assertEqual(qs.do_something(), "did something")