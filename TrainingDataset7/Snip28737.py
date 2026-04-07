def test_get_next_previous_by_date(self):
        """
        Regression tests for #8076
        get_(next/previous)_by_date should work
        """
        c1 = ArticleWithAuthor(
            headline="ArticleWithAuthor 1",
            author="Person 1",
            pub_date=datetime.datetime(2005, 8, 1, 3, 0),
        )
        c1.save()
        c2 = ArticleWithAuthor(
            headline="ArticleWithAuthor 2",
            author="Person 2",
            pub_date=datetime.datetime(2005, 8, 1, 10, 0),
        )
        c2.save()
        c3 = ArticleWithAuthor(
            headline="ArticleWithAuthor 3",
            author="Person 3",
            pub_date=datetime.datetime(2005, 8, 2),
        )
        c3.save()

        self.assertEqual(c1.get_next_by_pub_date(), c2)
        self.assertEqual(c2.get_next_by_pub_date(), c3)
        with self.assertRaises(ArticleWithAuthor.DoesNotExist):
            c3.get_next_by_pub_date()
        self.assertEqual(c3.get_previous_by_pub_date(), c2)
        self.assertEqual(c2.get_previous_by_pub_date(), c1)
        with self.assertRaises(ArticleWithAuthor.DoesNotExist):
            c1.get_previous_by_pub_date()