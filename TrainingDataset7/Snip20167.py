def test_overridden_get_transform(self):
        q = CustomModel.objects.filter(field__transformfunc_banana=3)
        self.assertIn("banana()", str(q.query))