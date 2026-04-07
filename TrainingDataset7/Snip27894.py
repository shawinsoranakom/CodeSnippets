def test_recursive_fks_get_col(self):
        class Foo(models.Model):
            bar = models.ForeignKey("Bar", models.CASCADE, primary_key=True)

        class Bar(models.Model):
            foo = models.ForeignKey(Foo, models.CASCADE, primary_key=True)

        with self.assertRaisesMessage(ValueError, "Cannot resolve output_field"):
            Foo._meta.get_field("bar").get_col("alias")