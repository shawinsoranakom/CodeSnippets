def test_empty_full_handling_disjunction(self):
        compiler = WhereNodeTest.MockCompiler()
        w = WhereNode(children=[NothingNode()], connector=OR)
        with self.assertRaises(EmptyResultSet):
            w.as_sql(compiler, connection)
        w.negate()
        with self.assertRaises(FullResultSet):
            w.as_sql(compiler, connection)
        w = WhereNode(children=[self.DummyNode(), self.DummyNode()], connector=OR)
        self.assertEqual(w.as_sql(compiler, connection), ("(dummy OR dummy)", []))
        w.negate()
        self.assertEqual(w.as_sql(compiler, connection), ("NOT (dummy OR dummy)", []))
        w = WhereNode(children=[NothingNode(), self.DummyNode()], connector=OR)
        self.assertEqual(w.as_sql(compiler, connection), ("dummy", []))
        w.negate()
        self.assertEqual(w.as_sql(compiler, connection), ("NOT (dummy)", []))