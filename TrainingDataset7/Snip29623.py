def test_exact_uuids(self):
        self.assertSequenceEqual(
            OtherTypesArrayModel.objects.filter(uuids=self.uuids), self.objs
        )