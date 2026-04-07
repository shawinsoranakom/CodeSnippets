def test_transform(self):
        with register_lookup(CharField, Lower):
            Author.objects.create(name="John Smith", alias="smithj")
            Author.objects.create(name="Rhonda")
            authors = Author.objects.filter(name__lower__exact="john smith")
            self.assertQuerySetEqual(
                authors.order_by("name"), ["John Smith"], lambda a: a.name
            )