def test_pointing_to_fk(self):
        class Foo(models.Model):
            pass

        class Bar(models.Model):
            foo_1 = models.ForeignKey(
                Foo, on_delete=models.CASCADE, related_name="bar_1"
            )
            foo_2 = models.ForeignKey(
                Foo, on_delete=models.CASCADE, related_name="bar_2"
            )

            class Meta:
                indexes = [
                    models.Index(fields=["foo_1_id", "foo_2"], name="index_name")
                ]

        self.assertEqual(Bar.check(databases=self.databases), [])