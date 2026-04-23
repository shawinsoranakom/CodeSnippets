def test_more_initial_data(self):
        """
        The extra argument works when the formset is pre-filled with initial
        data.
        """
        initial = [{"choice": "Calexico", "votes": 100}]
        ChoiceFormSet = formset_factory(Choice, extra=3)
        formset = ChoiceFormSet(initial=initial, auto_id=False, prefix="choices")
        self.assertHTMLEqual(
            "\n".join(form.as_ul() for form in formset.forms),
            '<li>Choice: <input type="text" name="choices-0-choice" value="Calexico">'
            "</li>"
            '<li>Votes: <input type="number" name="choices-0-votes" value="100"></li>'
            '<li>Choice: <input type="text" name="choices-1-choice"></li>'
            '<li>Votes: <input type="number" name="choices-1-votes"></li>'
            '<li>Choice: <input type="text" name="choices-2-choice"></li>'
            '<li>Votes: <input type="number" name="choices-2-votes"></li>'
            '<li>Choice: <input type="text" name="choices-3-choice"></li>'
            '<li>Votes: <input type="number" name="choices-3-votes"></li>',
        )
        # Retrieving an empty form works. Tt shows up in the form list.
        self.assertTrue(formset.empty_form.empty_permitted)
        self.assertHTMLEqual(
            formset.empty_form.as_ul(),
            """<li>Choice: <input type="text" name="choices-__prefix__-choice"></li>
<li>Votes: <input type="number" name="choices-__prefix__-votes"></li>""",
        )