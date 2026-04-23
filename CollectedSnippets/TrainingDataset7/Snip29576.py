def test_in_as_F_object(self):
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__in=[models.F("field")]),
            self.objs[:4],
        )