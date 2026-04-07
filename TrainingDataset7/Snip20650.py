def test_annotate_charfield(self):
        Author.objects.create(name="George. R. R. Martin")
        Author.objects.create(name="J. R. R. Tolkien")
        Author.objects.create(name="Terry Pratchett")
        authors = Author.objects.annotate(fullstop=StrIndex("name", Value("R.")))
        self.assertQuerySetEqual(
            authors.order_by("name"), [9, 4, 0], lambda a: a.fullstop
        )