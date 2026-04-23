def test_min_num_displaying_more_than_one_blank_form_with_zero_extra(self):
        """More than 1 empty form can be displayed using min_num."""
        ChoiceFormSet = formset_factory(Choice, extra=0, min_num=3)
        formset = ChoiceFormSet(auto_id=False, prefix="choices")
        self.assertHTMLEqual(
            "\n".join(form.as_ul() for form in formset.forms),
            """<li>Choice: <input type="text" name="choices-0-choice"></li>
<li>Votes: <input type="number" name="choices-0-votes"></li>
<li>Choice: <input type="text" name="choices-1-choice"></li>
<li>Votes: <input type="number" name="choices-1-votes"></li>
<li>Choice: <input type="text" name="choices-2-choice"></li>
<li>Votes: <input type="number" name="choices-2-votes"></li>""",
        )