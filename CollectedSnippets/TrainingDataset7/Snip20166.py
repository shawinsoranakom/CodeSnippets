def test_overridden_get_lookup(self):
        q = CustomModel.objects.filter(field__lookupfunc_monkeys=3)
        self.assertIn("monkeys()", str(q.query))