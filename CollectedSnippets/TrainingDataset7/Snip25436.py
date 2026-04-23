def test_on_delete_python_db_variants_auto_created(self):
        class SharedModel(models.Model):
            pass

        class Parent(models.Model):
            pass

        class Child(SharedModel):
            parent = models.ForeignKey(Parent, on_delete=models.DB_CASCADE)

        self.assertEqual(
            Child.check(databases=self.databases),
            [
                Error(
                    "The model cannot have related fields with both database-level and "
                    "Python-level on_delete variants.",
                    obj=Child,
                    id="models.E050",
                ),
            ],
        )