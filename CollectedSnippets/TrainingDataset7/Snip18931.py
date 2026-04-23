def test_save_expressions(self):
        article = Article(pub_date=Now())
        article.save()
        expected_num_queries = (
            0 if connection.features.can_return_columns_from_insert else 1
        )
        with self.assertNumQueries(expected_num_queries):
            article_pub_date = article.pub_date
        self.assertIsInstance(article_pub_date, datetime)
        # Sleep slightly to ensure a different database level NOW().
        time.sleep(0.1)
        article.pub_date = Now()
        article.save()
        expected_num_queries = (
            0 if connection.features.can_return_rows_from_update else 1
        )
        with self.assertNumQueries(expected_num_queries):
            self.assertIsInstance(article.pub_date, datetime)
        self.assertGreater(article.pub_date, article_pub_date)