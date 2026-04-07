def test_db_python_chain(self):
        class GrandParent(models.Model):
            pass

        class Parent(models.Model):
            grand_parent = models.ForeignKey(GrandParent, models.CASCADE)

        class Child(models.Model):
            parent = models.ForeignKey(Parent, models.DB_SET_NULL, null=True)

        field = Child._meta.get_field("parent")
        self.assertEqual(
            field.check(databases=self.databases),
            [
                Error(
                    "Field specifies database-level on_delete variant, but referenced "
                    "model uses Python-level variant.",
                    hint=(
                        "Use either database or Python on_delete variants uniformly in "
                        "the references chain."
                    ),
                    obj=field,
                    id="fields.E323",
                )
            ],
        )