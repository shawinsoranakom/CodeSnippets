def test_all_lookup(self):
        # Change values by changing the attributes, then calling save().
        self.a.headline = "Parrot programs in Python"
        self.a.save()

        # Article.objects.all() returns all the articles in the database.
        self.assertSequenceEqual(Article.objects.all(), [self.a])