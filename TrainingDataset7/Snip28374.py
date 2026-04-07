def test_multiple_field_unique_together(self):
        """
        When the same field is involved in multiple unique_together
        constraints, we need to make sure we don't remove the data for it
        before doing all the validation checking (not just failing after
        the first one).
        """

        class TripleForm(forms.ModelForm):
            class Meta:
                model = Triple
                fields = "__all__"

        Triple.objects.create(left=1, middle=2, right=3)

        form = TripleForm({"left": "1", "middle": "2", "right": "3"})
        self.assertFalse(form.is_valid())

        form = TripleForm({"left": "1", "middle": "3", "right": "1"})
        self.assertTrue(form.is_valid())