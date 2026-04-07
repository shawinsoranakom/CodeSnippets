def test_inherited_fields(self):
        """
        Regression test for #8825 and #9390
        Make sure all inherited fields (esp. m2m fields, in this case) appear
        on the child class.
        """
        m2mchildren = list(M2MChild.objects.filter(articles__isnull=False))
        self.assertEqual(m2mchildren, [])

        # Ordering should not include any database column more than once (this
        # is most likely to occur naturally with model inheritance, so we
        # check it here). Regression test for #9390. This necessarily pokes at
        # the SQL string for the query, since the duplicate problems are only
        # apparent at that late stage.
        qs = ArticleWithAuthor.objects.order_by("pub_date", "pk")
        sql = qs.query.get_compiler(qs.db).as_sql()[0]
        fragment = sql[sql.find("ORDER BY") :]
        pos = fragment.find("pub_date")
        self.assertEqual(fragment.find("pub_date", pos + 1), -1)