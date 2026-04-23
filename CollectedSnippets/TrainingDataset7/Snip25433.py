def test_func_unique_constraint_pointing_to_fk(self):
        class Foo(models.Model):
            id = models.CharField(primary_key=True, max_length=255)

        class Bar(models.Model):
            foo_1 = models.ForeignKey(Foo, models.CASCADE, related_name="bar_1")
            foo_2 = models.ForeignKey(Foo, models.CASCADE, related_name="bar_2")

            class Meta:
                constraints = [
                    models.UniqueConstraint(
                        Lower("foo_1_id"),
                        Lower("foo_2"),
                        name="name",
                    ),
                ]

        self.assertEqual(Bar.check(databases=self.databases), [])