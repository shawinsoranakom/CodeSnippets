def test_subquery_usage(self):
        with register_lookup(models.IntegerField, Div3Transform):
            Author.objects.create(name="a1", age=1)
            a2 = Author.objects.create(name="a2", age=2)
            Author.objects.create(name="a3", age=3)
            Author.objects.create(name="a4", age=4)
            qs = Author.objects.order_by("name").filter(
                id__in=Author.objects.filter(age__div3=2)
            )
            self.assertSequenceEqual(qs, [a2])