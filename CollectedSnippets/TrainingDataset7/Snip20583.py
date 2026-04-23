def test_function_as_filter(self):
        Author.objects.create(name="John Smith", alias="SMITHJ")
        Author.objects.create(name="Rhonda")
        self.assertQuerySetEqual(
            Author.objects.filter(alias=Upper(V("smithj"))),
            ["John Smith"],
            lambda x: x.name,
        )
        self.assertQuerySetEqual(
            Author.objects.exclude(alias=Upper(V("smithj"))),
            ["Rhonda"],
            lambda x: x.name,
        )