def test_saving_and_querying_for_json_null(self):
        obj = OtherTypesArrayModel.objects.create(json=[JSONNull(), JSONNull()])
        self.assertSequenceEqual(
            OtherTypesArrayModel.objects.filter(json__1=JSONNull()), [obj]
        )
        self.assertSequenceEqual(
            OtherTypesArrayModel.objects.filter(json__1__isnull=True), []
        )