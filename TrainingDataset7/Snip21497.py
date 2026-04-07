def test_compile_unresolved(self):
        # This test might need to be revisited later on if #25425 is enforced.
        compiler = Time.objects.all().query.get_compiler(connection=connection)
        value = Value("foo")
        self.assertEqual(value.as_sql(compiler, connection), ("%s", ("foo",)))
        value = Value("foo", output_field=CharField())
        self.assertEqual(value.as_sql(compiler, connection), ("%s", ("foo",)))