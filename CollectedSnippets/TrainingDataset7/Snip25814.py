def test_values_list_relations(self):
        args = ("name", "article__headline", "article__tag__name")
        self.assertSequenceEqual(
            Author.objects.values_list(*args).order_by(*args),
            [
                (self.au1.name, self.a1.headline, self.t1.name),
                (self.au1.name, self.a2.headline, self.t1.name),
                (self.au1.name, self.a3.headline, self.t1.name),
                (self.au1.name, self.a3.headline, self.t2.name),
                (self.au1.name, self.a4.headline, self.t2.name),
                (self.au2.name, self.a5.headline, self.t2.name),
                (self.au2.name, self.a5.headline, self.t3.name),
                (self.au2.name, self.a6.headline, self.t3.name),
                (self.au2.name, self.a7.headline, self.t3.name),
            ],
        )