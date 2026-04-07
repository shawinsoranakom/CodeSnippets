def test_order_by(self):
        Author.objects.create(name="Terry Pratchett")
        Author.objects.create(name="J. R. R. Tolkien")
        Author.objects.create(name="George. R. R. Martin")
        self.assertQuerySetEqual(
            Author.objects.order_by(StrIndex("name", Value("R.")).asc()),
            [
                "Terry Pratchett",
                "J. R. R. Tolkien",
                "George. R. R. Martin",
            ],
            lambda a: a.name,
        )
        self.assertQuerySetEqual(
            Author.objects.order_by(StrIndex("name", Value("R.")).desc()),
            [
                "George. R. R. Martin",
                "J. R. R. Tolkien",
                "Terry Pratchett",
            ],
            lambda a: a.name,
        )