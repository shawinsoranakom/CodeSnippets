def test_saving_and_querying_for_nested_json_nulls(self):
        obj = OtherTypesArrayModel.objects.create(json=[[None, 1], [None, 2]])
        self.assertSequenceEqual(
            OtherTypesArrayModel.objects.filter(json__1__0=None), [obj]
        )
        self.assertSequenceEqual(
            OtherTypesArrayModel.objects.filter(json__1__0__isnull=True), []
        )