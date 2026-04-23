def test_regex(self):
        # Create some articles with a bit more interesting headlines for
        # testing field lookups.
        Article.objects.all().delete()
        now = datetime.now()
        Article.objects.bulk_create(
            [
                Article(pub_date=now, headline="f"),
                Article(pub_date=now, headline="fo"),
                Article(pub_date=now, headline="foo"),
                Article(pub_date=now, headline="fooo"),
                Article(pub_date=now, headline="hey-Foo"),
                Article(pub_date=now, headline="bar"),
                Article(pub_date=now, headline="AbBa"),
                Article(pub_date=now, headline="baz"),
                Article(pub_date=now, headline="baxZ"),
            ]
        )
        # zero-or-more
        self.assertQuerySetEqual(
            Article.objects.filter(headline__regex=r"fo*"),
            Article.objects.filter(headline__in=["f", "fo", "foo", "fooo"]),
        )
        self.assertQuerySetEqual(
            Article.objects.filter(headline__iregex=r"fo*"),
            Article.objects.filter(headline__in=["f", "fo", "foo", "fooo", "hey-Foo"]),
        )
        # one-or-more
        self.assertQuerySetEqual(
            Article.objects.filter(headline__regex=r"fo+"),
            Article.objects.filter(headline__in=["fo", "foo", "fooo"]),
        )
        # wildcard
        self.assertQuerySetEqual(
            Article.objects.filter(headline__regex=r"fooo?"),
            Article.objects.filter(headline__in=["foo", "fooo"]),
        )
        # leading anchor
        self.assertQuerySetEqual(
            Article.objects.filter(headline__regex=r"^b"),
            Article.objects.filter(headline__in=["bar", "baxZ", "baz"]),
        )
        self.assertQuerySetEqual(
            Article.objects.filter(headline__iregex=r"^a"),
            Article.objects.filter(headline="AbBa"),
        )
        # trailing anchor
        self.assertQuerySetEqual(
            Article.objects.filter(headline__regex=r"z$"),
            Article.objects.filter(headline="baz"),
        )
        self.assertQuerySetEqual(
            Article.objects.filter(headline__iregex=r"z$"),
            Article.objects.filter(headline__in=["baxZ", "baz"]),
        )
        # character sets
        self.assertQuerySetEqual(
            Article.objects.filter(headline__regex=r"ba[rz]"),
            Article.objects.filter(headline__in=["bar", "baz"]),
        )
        self.assertQuerySetEqual(
            Article.objects.filter(headline__regex=r"ba.[RxZ]"),
            Article.objects.filter(headline="baxZ"),
        )
        self.assertQuerySetEqual(
            Article.objects.filter(headline__iregex=r"ba[RxZ]"),
            Article.objects.filter(headline__in=["bar", "baxZ", "baz"]),
        )

        # and more articles:
        Article.objects.bulk_create(
            [
                Article(pub_date=now, headline="foobar"),
                Article(pub_date=now, headline="foobaz"),
                Article(pub_date=now, headline="ooF"),
                Article(pub_date=now, headline="foobarbaz"),
                Article(pub_date=now, headline="zoocarfaz"),
                Article(pub_date=now, headline="barfoobaz"),
                Article(pub_date=now, headline="bazbaRFOO"),
            ]
        )

        # alternation
        self.assertQuerySetEqual(
            Article.objects.filter(headline__regex=r"oo(f|b)"),
            Article.objects.filter(
                headline__in=[
                    "barfoobaz",
                    "foobar",
                    "foobarbaz",
                    "foobaz",
                ]
            ),
        )
        self.assertQuerySetEqual(
            Article.objects.filter(headline__iregex=r"oo(f|b)"),
            Article.objects.filter(
                headline__in=[
                    "barfoobaz",
                    "foobar",
                    "foobarbaz",
                    "foobaz",
                    "ooF",
                ]
            ),
        )
        self.assertQuerySetEqual(
            Article.objects.filter(headline__regex=r"^foo(f|b)"),
            Article.objects.filter(headline__in=["foobar", "foobarbaz", "foobaz"]),
        )

        # greedy matching
        self.assertQuerySetEqual(
            Article.objects.filter(headline__regex=r"b.*az"),
            Article.objects.filter(
                headline__in=[
                    "barfoobaz",
                    "baz",
                    "bazbaRFOO",
                    "foobarbaz",
                    "foobaz",
                ]
            ),
        )
        self.assertQuerySetEqual(
            Article.objects.filter(headline__iregex=r"b.*ar"),
            Article.objects.filter(
                headline__in=[
                    "bar",
                    "barfoobaz",
                    "bazbaRFOO",
                    "foobar",
                    "foobarbaz",
                ]
            ),
        )