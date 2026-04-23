def test_no_chunked_reads(self):
        """
        If the database backend doesn't support chunked reads, then the
        result of SQLCompiler.execute_sql() is a list.
        """
        qs = Article.objects.all()
        compiler = qs.query.get_compiler(using=qs.db)
        features = connections[qs.db].features
        with mock.patch.object(features, "can_use_chunked_reads", False):
            result = compiler.execute_sql(chunked_fetch=True)
        self.assertIsInstance(result, list)