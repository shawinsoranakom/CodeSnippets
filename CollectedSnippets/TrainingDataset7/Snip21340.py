def test_slicing_of_f_expressions_with_annotate(self):
        qs = Company.objects.annotate(
            first_three=F("name")[:3],
            after_three=F("name")[3:],
            random_four=F("name")[2:5],
            first_letter_slice=F("name")[:1],
            first_letter_index=F("name")[0],
        )
        tests = [
            ("first_three", ["Exa", "Foo", "Tes"]),
            ("after_three", ["mple Inc.", "bar Ltd.", "t GmbH"]),
            ("random_four", ["amp", "oba", "st "]),
            ("first_letter_slice", ["E", "F", "T"]),
            ("first_letter_index", ["E", "F", "T"]),
        ]
        for annotation, expected in tests:
            with self.subTest(annotation):
                self.assertCountEqual(qs.values_list(annotation, flat=True), expected)