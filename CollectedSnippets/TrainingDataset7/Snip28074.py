def test_key_quoted_string(self):
        self.assertEqual(
            NullableJSONModel.objects.filter(value__o='"quoted"').get(),
            self.objs[4],
        )