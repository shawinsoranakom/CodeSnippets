def _make_authors(self, n):
        Author.objects.all().delete()
        for i in range(n):
            Author.objects.create(name="Author %02i" % i, slug="a%s" % i)