def test_overridden_get_transform_chain(self):
        q = CustomModel.objects.filter(
            field__transformfunc_banana__transformfunc_pear=3
        )
        self.assertIn("pear()", str(q.query))