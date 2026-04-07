def test_grouping_by_annotations_with_array_field_param(self):
        value = models.Value([1], output_field=ArrayField(models.IntegerField()))
        self.assertEqual(
            NullableIntegerArrayModel.objects.annotate(
                array_length=models.Func(
                    value,
                    1,
                    function="ARRAY_LENGTH",
                    output_field=models.IntegerField(),
                ),
            )
            .values("array_length")
            .annotate(
                count=models.Count("pk"),
            )
            .get()["array_length"],
            1,
        )