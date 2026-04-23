def test_filtering(self):
        Author.objects.create(name="George. R. R. Martin")
        Author.objects.create(name="Terry Pratchett")
        self.assertQuerySetEqual(
            Author.objects.annotate(middle_name=StrIndex("name", Value("R."))).filter(
                middle_name__gt=0
            ),
            ["George. R. R. Martin"],
            lambda a: a.name,
        )