def test_through_db_table_mutually_exclusive(self):
        class Child(models.Model):
            pass

        class Through(models.Model):
            referred = models.ForeignKey(Child, on_delete=models.CASCADE)
            referent = models.ForeignKey(Child, on_delete=models.CASCADE)

        msg = "Cannot specify a db_table if an intermediary model is used."
        with self.assertRaisesMessage(ValueError, msg):

            class MyModel(models.Model):
                m2m = models.ManyToManyField(
                    Child,
                    through="Through",
                    db_table="custom_name",
                )