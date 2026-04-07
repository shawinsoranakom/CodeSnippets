def setUp(self):
        data = {
            "choices-TOTAL_FORMS": "1",
            "choices-INITIAL_FORMS": "0",
            "choices-MIN_NUM_FORMS": "0",
            "choices-MAX_NUM_FORMS": "0",
            "choices-0-choice": "Calexico",
            "choices-0-votes": "100",
        }
        self.formset = ChoiceFormSet(data, auto_id=False, prefix="choices")
        self.management_form_html = (
            '<input type="hidden" name="choices-TOTAL_FORMS" value="1">'
            '<input type="hidden" name="choices-INITIAL_FORMS" value="0">'
            '<input type="hidden" name="choices-MIN_NUM_FORMS" value="0">'
            '<input type="hidden" name="choices-MAX_NUM_FORMS" value="0">'
        )