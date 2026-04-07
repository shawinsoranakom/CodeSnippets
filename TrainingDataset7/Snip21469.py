def test_datetime_subtraction_with_annotate_and_no_output_field(self):
        test_set = Experiment.objects.annotate(
            calculated_duration=F("end") - F("start")
        )
        self.assertEqual(
            [e.calculated_duration for e in test_set],
            [e.end - e.start for e in test_set],
        )