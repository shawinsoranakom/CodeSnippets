def test_deep_lookup_transform(self):
        self.assertCountEqual(
            NullableJSONModel.objects.filter(value__c__gt=2),
            [self.objs[3], self.objs[4]],
        )
        self.assertCountEqual(
            NullableJSONModel.objects.filter(value__c__gt=2.33),
            [self.objs[3], self.objs[4]],
        )
        self.assertIs(NullableJSONModel.objects.filter(value__c__lt=5).exists(), False)