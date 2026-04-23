def test_subquery_sql(self):
        employees = Employee.objects.all()
        employees_subquery = Subquery(employees)
        self.assertIs(employees_subquery.query.subquery, True)
        self.assertIs(employees.query.subquery, False)
        compiler = employees_subquery.query.get_compiler(connection=connection)
        sql, _ = employees_subquery.as_sql(compiler, connection)
        self.assertIn("(SELECT ", sql)