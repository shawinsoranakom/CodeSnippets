def test_related_field(self):
        author = Author.objects.create(name="John Smith", age=45)
        Fan.objects.create(name="Margaret", age=50, author=author)
        authors = Author.objects.annotate(highest_age=Greatest("age", "fans__age"))
        self.assertEqual(authors.first().highest_age, 50)