def test_min_num_displaying_more_than_one_blank_form(self):
        """
        More than 1 empty form can also be displayed using formset_factory's
        min_num argument. It will (essentially) increment the extra argument.
        """
        ChoiceFormSet = formset_factory(Choice, extra=1, min_num=1)
        formset = ChoiceFormSet(auto_id=False, prefix="choices")
        # Min_num forms are required; extra forms can be empty.
        self.assertFalse(formset.forms[0].empty_permitted)
        self.assertTrue(formset.forms[1].empty_permitted)
        self.assertHTMLEqual(
            "\n".join(form.as_ul() for form in formset.forms),
            """<li>Choice: <input type="text" name="choices-0-choice"></li>
<li>Votes: <input type="number" name="choices-0-votes"></li>
<li>Choice: <input type="text" name="choices-1-choice"></li>
<li>Votes: <input type="number" name="choices-1-votes"></li>""",
        )