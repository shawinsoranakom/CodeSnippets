def test_slicing_of_f_expressions_with_annotate(self):
        IntegerArrayModel.objects.create(field=[1, 2, 3])
        annotated = IntegerArrayModel.objects.annotate(
            first_two=F("field")[:2],
            after_two=F("field")[2:],
            random_two=F("field")[1:3],
        ).get()
        self.assertEqual(annotated.first_two, [1, 2])
        self.assertEqual(annotated.after_two, [3])
        self.assertEqual(annotated.random_two, [2, 3])