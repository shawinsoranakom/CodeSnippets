def test_empty_full_handling_conjunction(self):
        compiler = WhereNodeTest.MockCompiler()
        w = WhereNode(children=[NothingNode()])
        with self.assertRaises(EmptyResultSet):
            w.as_sql(compiler, connection)
        w.negate()
        with self.assertRaises(FullResultSet):
            w.as_sql(compiler, connection)
        w = WhereNode(children=[self.DummyNode(), self.DummyNode()])
        self.assertEqual(w.as_sql(compiler, connection), ("(dummy AND dummy)", []))
        w.negate()
        self.assertEqual(w.as_sql(compiler, connection), ("NOT (dummy AND dummy)", []))
        w = WhereNode(children=[NothingNode(), self.DummyNode()])
        with self.assertRaises(EmptyResultSet):
            w.as_sql(compiler, connection)
        w.negate()
        with self.assertRaises(FullResultSet):
            w.as_sql(compiler, connection)