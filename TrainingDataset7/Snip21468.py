def test_datetime_and_duration_field_addition_with_annotate_and_no_output_field(
        self,
    ):
        test_set = Experiment.objects.annotate(
            estimated_end=F("start") + F("estimated_time")
        )
        self.assertEqual(
            [e.estimated_end for e in test_set],
            [e.start + e.estimated_time for e in test_set],
        )