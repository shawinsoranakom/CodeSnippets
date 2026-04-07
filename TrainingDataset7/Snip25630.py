def test_db_cascade_required_db_features(self):
        class Parent(models.Model):
            pass

        class Child(models.Model):
            parent = models.ForeignKey(Parent, models.DB_CASCADE)

            class Meta:
                required_db_features = {"supports_on_delete_db_cascade"}

        field = Child._meta.get_field("parent")
        self.assertEqual(field.check(databases=self.databases), [])