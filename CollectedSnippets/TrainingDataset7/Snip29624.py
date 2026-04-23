def test_exact_decimals(self):
        self.assertSequenceEqual(
            OtherTypesArrayModel.objects.filter(decimals=self.decimals), self.objs
        )