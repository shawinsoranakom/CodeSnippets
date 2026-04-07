def test_isnull_lookup_in_filter(self):
        self.assertSequenceEqual(
            Season.objects.filter(IsNull(F("nulled_text_field"), False)),
            [self.s2],
        )
        self.assertCountEqual(
            Season.objects.filter(IsNull(F("nulled_text_field"), True)),
            [self.s1, self.s3],
        )