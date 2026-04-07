def test_contains_expressions(self):
        c = BaseConstraint(name="name")
        self.assertIs(c.contains_expressions, False)