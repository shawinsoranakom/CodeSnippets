def test_fields_for_model_applies_limit_choices_to(self):
        fields = fields_for_model(StumpJoke, ["has_fooled_today"])
        self.assertSequenceEqual(fields["has_fooled_today"].queryset, [self.threepwood])