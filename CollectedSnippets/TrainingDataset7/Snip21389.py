def test_explicit_output_field(self):
        class FuncA(Func):
            output_field = CharField()

        class FuncB(Func):
            pass

        expr = FuncB(FuncA())
        self.assertEqual(expr.output_field, FuncA.output_field)