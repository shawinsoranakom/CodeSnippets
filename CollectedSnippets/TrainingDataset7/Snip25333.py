def test_func_index_pointing_to_fk(self):
        class Foo(models.Model):
            pass

        class Bar(models.Model):
            foo_1 = models.ForeignKey(Foo, models.CASCADE, related_name="bar_1")
            foo_2 = models.ForeignKey(Foo, models.CASCADE, related_name="bar_2")

            class Meta:
                indexes = [
                    models.Index(Lower("foo_1_id"), Lower("foo_2"), name="index_name"),
                ]

        self.assertEqual(Bar.check(databases=self.databases), [])