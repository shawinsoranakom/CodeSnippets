def test_formsets_with_ordering(self):
        """
        formset_factory's can_order argument adds an integer field to each
        form. When form validation succeeds,
            [form.cleaned_data for form in formset.forms]
        will have the data in the correct order specified by the ordering
        fields. If a number is duplicated in the set of ordering fields, for
        instance form 0 and form 3 are both marked as 1, then the form index
        used as a secondary ordering criteria. In order to put something at the
        front of the list, you'd need to set its order to 0.
        """
        ChoiceFormSet = formset_factory(Choice, can_order=True)
        initial = [
            {"choice": "Calexico", "votes": 100},
            {"choice": "Fergie", "votes": 900},
        ]
        formset = ChoiceFormSet(initial=initial, auto_id=False, prefix="choices")
        self.assertHTMLEqual(
            "\n".join(form.as_ul() for form in formset.forms),
            '<li>Choice: <input type="text" name="choices-0-choice" value="Calexico">'
            "</li>"
            '<li>Votes: <input type="number" name="choices-0-votes" value="100"></li>'
            '<li>Order: <input type="number" name="choices-0-ORDER" value="1"></li>'
            '<li>Choice: <input type="text" name="choices-1-choice" value="Fergie">'
            "</li>"
            '<li>Votes: <input type="number" name="choices-1-votes" value="900"></li>'
            '<li>Order: <input type="number" name="choices-1-ORDER" value="2"></li>'
            '<li>Choice: <input type="text" name="choices-2-choice"></li>'
            '<li>Votes: <input type="number" name="choices-2-votes"></li>'
            '<li>Order: <input type="number" name="choices-2-ORDER"></li>',
        )
        data = {
            "choices-TOTAL_FORMS": "3",  # the number of forms rendered
            "choices-INITIAL_FORMS": "2",  # the number of forms with initial data
            "choices-MIN_NUM_FORMS": "0",  # min number of forms
            "choices-MAX_NUM_FORMS": "0",  # max number of forms
            "choices-0-choice": "Calexico",
            "choices-0-votes": "100",
            "choices-0-ORDER": "1",
            "choices-1-choice": "Fergie",
            "choices-1-votes": "900",
            "choices-1-ORDER": "2",
            "choices-2-choice": "The Decemberists",
            "choices-2-votes": "500",
            "choices-2-ORDER": "0",
        }
        formset = ChoiceFormSet(data, auto_id=False, prefix="choices")
        self.assertTrue(formset.is_valid())
        self.assertEqual(
            [form.cleaned_data for form in formset.ordered_forms],
            [
                {"votes": 500, "ORDER": 0, "choice": "The Decemberists"},
                {"votes": 100, "ORDER": 1, "choice": "Calexico"},
                {"votes": 900, "ORDER": 2, "choice": "Fergie"},
            ],
        )