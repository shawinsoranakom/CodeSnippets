def test_func_transform_bilateral_multivalue(self):
        with register_lookup(CharField, UpperBilateral):
            Author.objects.create(name="John Smith", alias="smithj")
            Author.objects.create(name="Rhonda")
            authors = Author.objects.filter(name__upper__in=["john smith", "rhonda"])
            self.assertQuerySetEqual(
                authors.order_by("name"),
                [
                    "John Smith",
                    "Rhonda",
                ],
                lambda a: a.name,
            )