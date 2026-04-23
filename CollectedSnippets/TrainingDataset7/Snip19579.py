def test_foreign_object_can_refer_composite_pk(self):
        class Foo(models.Model):
            pass

        class Bar(models.Model):
            pk = models.CompositePrimaryKey("foo_id", "id")
            foo = models.ForeignKey(Foo, on_delete=models.CASCADE)
            id = models.IntegerField()

        class Baz(models.Model):
            pk = models.CompositePrimaryKey("foo_id", "id")
            foo = models.ForeignKey(Foo, on_delete=models.CASCADE)
            id = models.IntegerField()
            bar_id = models.IntegerField()
            bar = models.ForeignObject(
                Bar,
                on_delete=models.CASCADE,
                from_fields=("foo_id", "bar_id"),
                to_fields=("foo_id", "id"),
            )

        self.assertEqual(Foo.check(databases=self.databases), [])
        self.assertEqual(Bar.check(databases=self.databases), [])
        self.assertEqual(Baz.check(databases=self.databases), [])