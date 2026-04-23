def test_proxy_model_can_subclass_model_with_composite_pk(self):
        class Foo(models.Model):
            pk = models.CompositePrimaryKey("a", "b")
            a = models.SmallIntegerField()
            b = models.SmallIntegerField()

        class Bar(Foo):
            class Meta:
                proxy = True

        self.assertEqual(Foo.check(databases=self.databases), [])
        self.assertEqual(Bar.check(databases=self.databases), [])