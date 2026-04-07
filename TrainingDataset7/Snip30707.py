def test_ticket_18414(self):
        Article.objects.create(name="one", created=datetime.datetime.now())
        Article.objects.create(name="one", created=datetime.datetime.now())
        Article.objects.create(name="two", created=datetime.datetime.now())
        self.assertTrue(Article.objects.exists())
        self.assertTrue(Article.objects.distinct().exists())
        self.assertTrue(Article.objects.distinct()[1:3].exists())
        self.assertFalse(Article.objects.distinct()[1:1].exists())