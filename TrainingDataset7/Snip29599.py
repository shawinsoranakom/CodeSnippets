def test_len_empty_array(self):
        obj = NullableIntegerArrayModel.objects.create(field=[])
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__len=0), [obj]
        )