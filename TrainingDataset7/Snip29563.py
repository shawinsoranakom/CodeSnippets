def test_empty_list(self):
        NullableIntegerArrayModel.objects.create(field=[])
        obj = (
            NullableIntegerArrayModel.objects.annotate(
                empty_array=models.Value(
                    [], output_field=ArrayField(models.IntegerField())
                ),
            )
            .filter(field=models.F("empty_array"))
            .get()
        )
        self.assertEqual(obj.field, [])
        self.assertEqual(obj.empty_array, [])