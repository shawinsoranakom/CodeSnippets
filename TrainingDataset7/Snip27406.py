def test_alter_index_together_remove(self):
        operation = migrations.AlterIndexTogether("Pony", None)
        self.assertEqual(
            operation.describe(), "Alter index_together for Pony (0 constraint(s))"
        )
        self.assertEqual(
            operation.formatted_description(),
            "~ Alter index_together for Pony (0 constraint(s))",
        )