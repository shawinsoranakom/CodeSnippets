def test_overlap_charfield_including_expression(self):
        obj_1 = CharArrayModel.objects.create(field=["TEXT", "lower text"])
        obj_2 = CharArrayModel.objects.create(field=["lower text", "TEXT"])
        CharArrayModel.objects.create(field=["lower text", "text"])
        self.assertSequenceEqual(
            CharArrayModel.objects.filter(
                field__overlap=[
                    Upper(Value("text")),
                    "other",
                ]
            ),
            [obj_1, obj_2],
        )