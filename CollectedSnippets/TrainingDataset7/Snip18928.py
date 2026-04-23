def test_multiple_objects_max_num_fetched(self):
        max_results = MAX_GET_RESULTS - 1
        Article.objects.bulk_create(
            Article(headline="Area %s" % i, pub_date=datetime(2005, 7, 28))
            for i in range(max_results)
        )
        self.assertRaisesMessage(
            MultipleObjectsReturned,
            "get() returned more than one Article -- it returned %d!" % max_results,
            Article.objects.get,
            headline__startswith="Area",
        )
        Article.objects.create(
            headline="Area %s" % max_results, pub_date=datetime(2005, 7, 28)
        )
        self.assertRaisesMessage(
            MultipleObjectsReturned,
            "get() returned more than one Article -- it returned more than %d!"
            % max_results,
            Article.objects.get,
            headline__startswith="Area",
        )