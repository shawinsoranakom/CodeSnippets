def test_alter_unique_together_remove(self):
        operation = migrations.AlterUniqueTogether("Pony", None)
        self.assertEqual(
            operation.describe(), "Alter unique_together for Pony (0 constraint(s))"
        )