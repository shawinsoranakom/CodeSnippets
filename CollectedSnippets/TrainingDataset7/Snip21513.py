def test_expressions(self):
        self.assertEqual(
            repr(Case(When(a=1))),
            "<Case: CASE WHEN <Q: (AND: ('a', 1))> THEN Value(None), ELSE Value(None)>",
        )
        self.assertEqual(
            repr(When(Q(age__gte=18), then=Value("legal"))),
            "<When: WHEN <Q: (AND: ('age__gte', 18))> THEN Value('legal')>",
        )
        self.assertEqual(repr(Col("alias", "field")), "Col(alias, field)")
        self.assertEqual(
            repr(ColPairs("alias", ["t1", "t2"], ["s1", "s2"], "f")),
            "ColPairs('alias', ['t1', 't2'], ['s1', 's2'], 'f')",
        )
        self.assertEqual(repr(F("published")), "F(published)")
        self.assertEqual(
            repr(F("cost") + F("tax")), "<CombinedExpression: F(cost) + F(tax)>"
        )
        self.assertEqual(
            repr(ExpressionWrapper(F("cost") + F("tax"), IntegerField())),
            "ExpressionWrapper(F(cost) + F(tax))",
        )
        self.assertEqual(
            repr(Func("published", function="TO_CHAR")),
            "Func(F(published), function=TO_CHAR)",
        )
        self.assertEqual(
            repr(F("published")[0:2]), "Sliced(F(published), slice(0, 2, None))"
        )
        self.assertEqual(
            repr(OuterRef("name")[1:5]), "Sliced(OuterRef(name), slice(1, 5, None))"
        )
        self.assertEqual(repr(OrderBy(Value(1))), "OrderBy(Value(1), descending=False)")
        self.assertEqual(repr(RawSQL("table.col", [])), "RawSQL(table.col, [])")
        self.assertEqual(
            repr(Ref("sum_cost", Sum("cost"))), "Ref(sum_cost, Sum(F(cost)))"
        )
        self.assertEqual(repr(Value(1)), "Value(1)")
        self.assertEqual(
            repr(ExpressionList(F("col"), F("anothercol"))),
            "ExpressionList(F(col), F(anothercol))",
        )
        self.assertEqual(
            repr(ExpressionList(OrderBy(F("col"), descending=False))),
            "ExpressionList(OrderBy(F(col), descending=False))",
        )