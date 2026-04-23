def test_mixed_char_date_with_annotate(self):
        queryset = Experiment.objects.annotate(nonsense=F("name") + F("assigned"))
        msg = (
            "Cannot infer type of '+' expression involving these types: CharField, "
            "DateField. You must set output_field."
        )
        with self.assertRaisesMessage(FieldError, msg):
            list(queryset)