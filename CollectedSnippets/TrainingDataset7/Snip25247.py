def test_table_with_func_unique_constraint(self):
        out = StringIO()
        call_command("inspectdb", "inspectdb_funcuniqueconstraint", stdout=out)
        output = out.getvalue()
        self.assertIn("class InspectdbFuncuniqueconstraint(models.Model):", output)