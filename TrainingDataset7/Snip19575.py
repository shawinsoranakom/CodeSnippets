def test_composite_pk_can_include_fk_name(self):
        class Foo(models.Model):
            pass

        class Bar(models.Model):
            pk = models.CompositePrimaryKey("foo", "id")
            foo = models.ForeignKey(Foo, on_delete=models.CASCADE)
            id = models.SmallIntegerField()

        self.assertEqual(Foo.check(databases=self.databases), [])
        self.assertEqual(Bar.check(databases=self.databases), [])