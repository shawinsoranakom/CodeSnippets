def test_non_nullable_fk_not_promoted(self):
        qs = ObjectB.objects.values("objecta__name")
        self.assertIn(" INNER JOIN ", str(qs.query))