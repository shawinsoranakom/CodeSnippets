def test_order_by_f_expression_duplicates(self):
        """
        A column may only be included once (the first occurrence) so we check
        to ensure there are no duplicates by inspecting the SQL.
        """
        qs = Article.objects.order_by(F("headline").asc(), F("headline").desc())
        sql = str(qs.query).upper()
        fragment = sql[sql.find("ORDER BY") :]
        self.assertEqual(fragment.count("HEADLINE"), 1)
        self.assertQuerySetEqual(
            qs,
            [
                "Article 1",
                "Article 2",
                "Article 3",
                "Article 4",
            ],
            attrgetter("headline"),
        )
        qs = Article.objects.order_by(F("headline").desc(), F("headline").asc())
        sql = str(qs.query).upper()
        fragment = sql[sql.find("ORDER BY") :]
        self.assertEqual(fragment.count("HEADLINE"), 1)
        self.assertQuerySetEqual(
            qs,
            [
                "Article 4",
                "Article 3",
                "Article 2",
                "Article 1",
            ],
            attrgetter("headline"),
        )