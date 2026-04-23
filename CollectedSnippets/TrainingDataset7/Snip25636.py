def test_python_db_chain(self):
        class GrandParent(models.Model):
            pass

        class Parent(models.Model):
            grand_parent = models.ForeignKey(GrandParent, models.DB_CASCADE)

        class Child(models.Model):
            parent = models.ForeignKey(Parent, models.RESTRICT)

        field = Child._meta.get_field("parent")
        self.assertEqual(
            field.check(databases=self.databases),
            [
                Error(
                    "Field specifies Python-level on_delete variant, but referenced "
                    "model uses database-level variant.",
                    hint=(
                        "Use either database or Python on_delete variants uniformly in "
                        "the references chain."
                    ),
                    obj=field,
                    id="fields.E323",
                )
            ],
        )