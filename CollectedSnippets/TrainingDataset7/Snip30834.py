def test_empty_nodes(self):
        compiler = WhereNodeTest.MockCompiler()
        empty_w = WhereNode()
        w = WhereNode(children=[empty_w, empty_w])
        with self.assertRaises(FullResultSet):
            w.as_sql(compiler, connection)
        w.negate()
        with self.assertRaises(EmptyResultSet):
            w.as_sql(compiler, connection)
        w.connector = OR
        with self.assertRaises(EmptyResultSet):
            w.as_sql(compiler, connection)
        w.negate()
        with self.assertRaises(FullResultSet):
            w.as_sql(compiler, connection)
        w = WhereNode(children=[empty_w, NothingNode()], connector=OR)
        with self.assertRaises(FullResultSet):
            w.as_sql(compiler, connection)
        w = WhereNode(children=[empty_w, NothingNode()], connector=AND)
        with self.assertRaises(EmptyResultSet):
            w.as_sql(compiler, connection)