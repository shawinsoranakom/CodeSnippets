def test_displaying_more_than_one_blank_form(self):
        """
        More than 1 empty form can be displayed using formset_factory's
        `extra` argument.
        """
        ChoiceFormSet = formset_factory(Choice, extra=3)
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
        # Since every form was displayed as blank, they are also accepted as
        # blank. This may seem a little strange, but min_num is used to require
        # a minimum number of forms to be completed.
        data = {
            "choices-TOTAL_FORMS": "3",  # the number of forms rendered
            "choices-INITIAL_FORMS": "0",  # the number of forms with initial data
            "choices-MIN_NUM_FORMS": "0",  # min number of forms
            "choices-MAX_NUM_FORMS": "0",  # max number of forms
            "choices-0-choice": "",
            "choices-0-votes": "",
            "choices-1-choice": "",
            "choices-1-votes": "",
            "choices-2-choice": "",
            "choices-2-votes": "",
        }
        formset = ChoiceFormSet(data, auto_id=False, prefix="choices")
        self.assertTrue(formset.is_valid())
        self.assertEqual([form.cleaned_data for form in formset.forms], [{}, {}, {}])