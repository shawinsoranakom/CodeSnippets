def test_ticket_18414_distinct_on(self):
        Article.objects.create(name="one", created=datetime.datetime.now())
        Article.objects.create(name="one", created=datetime.datetime.now())
        Article.objects.create(name="two", created=datetime.datetime.now())
        self.assertTrue(Article.objects.distinct("name").exists())
        self.assertTrue(Article.objects.distinct("name")[1:2].exists())
        self.assertFalse(Article.objects.distinct("name")[2:3].exists())