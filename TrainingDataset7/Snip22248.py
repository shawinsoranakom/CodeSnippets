def test_close_connection_after_loaddata(self):
        """
        Test for ticket #7572 -- MySQL has a problem if the same connection is
        used to create tables, load data, and then query over that data.
        To compensate, we close the connection after running loaddata.
        This ensures that a new connection is opened when test queries are
        issued.
        """
        management.call_command(
            "loaddata",
            "big-fixture.json",
            verbosity=0,
        )
        articles = Article.objects.exclude(id=9)
        self.assertEqual(
            list(articles.values_list("id", flat=True)), [1, 2, 3, 4, 5, 6, 7, 8]
        )
        # Just for good measure, run the same query again.
        # Under the influence of ticket #7572, this will
        # give a different result to the previous call.
        self.assertEqual(
            list(articles.values_list("id", flat=True)), [1, 2, 3, 4, 5, 6, 7, 8]
        )