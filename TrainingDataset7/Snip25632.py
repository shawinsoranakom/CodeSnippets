def test_db_set_default_required_db_features(self):
        class Parent(models.Model):
            pass

        class Child(models.Model):
            parent = models.ForeignKey(
                Parent, models.DB_SET_DEFAULT, db_default=models.Value(1)
            )

            class Meta:
                required_db_features = {"supports_on_delete_db_default"}

        field = Child._meta.get_field("parent")
        self.assertEqual(field.check(databases=self.databases), [])