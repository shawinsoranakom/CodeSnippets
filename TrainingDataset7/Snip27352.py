def test_alter_model_table_none(self):
        """
        Tests the AlterModelTable operation if the table name is set to None.
        """
        operation = migrations.AlterModelTable("Pony", None)
        self.assertEqual(operation.describe(), "Rename table for Pony to (default)")