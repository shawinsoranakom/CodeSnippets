def test_contained_by_including_F_object(self):
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(
                field__contained_by=[models.F("order"), 2]
            ),
            self.objs[:3],
        )