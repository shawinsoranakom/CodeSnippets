def test_delete_and_access_field(self):
        # Accessing a field after it's deleted from a model reloads its value.
        pub_date = datetime.now()
        article = Article.objects.create(headline="foo", pub_date=pub_date)
        new_pub_date = article.pub_date + timedelta(days=10)
        article.headline = "bar"
        article.pub_date = new_pub_date
        del article.headline
        with self.assertNumQueries(1):
            self.assertEqual(article.headline, "foo")
        # Fields that weren't deleted aren't reloaded.
        self.assertEqual(article.pub_date, new_pub_date)