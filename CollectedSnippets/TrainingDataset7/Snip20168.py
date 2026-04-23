def test_overridden_get_lookup_chain(self):
        q = CustomModel.objects.filter(
            field__transformfunc_banana__lookupfunc_elephants=3
        )
        self.assertIn("elephants()", str(q.query))