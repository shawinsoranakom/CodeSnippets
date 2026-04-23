def test_extract_duration_without_native_duration_field(self):
        msg = "Extract requires native DurationField database support."
        with self.assertRaisesMessage(ValueError, msg):
            list(DTModel.objects.annotate(extracted=Extract("duration", "second")))