def test_formset_with_ordering_and_deletion(self):
        """FormSets with ordering + deletion."""
        ChoiceFormSet = formset_factory(Choice, can_order=True, can_delete=True)
        initial = [
            {"choice": "Calexico", "votes": 100},
            {"choice": "Fergie", "votes": 900},
            {"choice": "The Decemberists", "votes": 500},
        ]
        formset = ChoiceFormSet(initial=initial, auto_id=False, prefix="choices")
        self.assertHTMLEqual(
            "\n".join(form.as_ul() for form in formset.forms),
            '<li>Choice: <input type="text" name="choices-0-choice" value="Calexico">'
            "</li>"
            '<li>Votes: <input type="number" name="choices-0-votes" value="100"></li>'
            '<li>Order: <input type="number" name="choices-0-ORDER" value="1"></li>'
            '<li>Delete: <input type="checkbox" name="choices-0-DELETE"></li>'
            '<li>Choice: <input type="text" name="choices-1-choice" value="Fergie">'
            "</li>"
            '<li>Votes: <input type="number" name="choices-1-votes" value="900"></li>'
            '<li>Order: <input type="number" name="choices-1-ORDER" value="2"></li>'
            '<li>Delete: <input type="checkbox" name="choices-1-DELETE"></li>'
            '<li>Choice: <input type="text" name="choices-2-choice" '
            'value="The Decemberists"></li>'
            '<li>Votes: <input type="number" name="choices-2-votes" value="500"></li>'
            '<li>Order: <input type="number" name="choices-2-ORDER" value="3"></li>'
            '<li>Delete: <input type="checkbox" name="choices-2-DELETE"></li>'
            '<li>Choice: <input type="text" name="choices-3-choice"></li>'
            '<li>Votes: <input type="number" name="choices-3-votes"></li>'
            '<li>Order: <input type="number" name="choices-3-ORDER"></li>'
            '<li>Delete: <input type="checkbox" name="choices-3-DELETE"></li>',
        )
        # Let's delete Fergie, and put The Decemberists ahead of Calexico.
        data = {
            "choices-TOTAL_FORMS": "4",  # the number of forms rendered
            "choices-INITIAL_FORMS": "3",  # the number of forms with initial data
            "choices-MIN_NUM_FORMS": "0",  # min number of forms
            "choices-MAX_NUM_FORMS": "0",  # max number of forms
            "choices-0-choice": "Calexico",
            "choices-0-votes": "100",
            "choices-0-ORDER": "1",
            "choices-0-DELETE": "",
            "choices-1-choice": "Fergie",
            "choices-1-votes": "900",
            "choices-1-ORDER": "2",
            "choices-1-DELETE": "on",
            "choices-2-choice": "The Decemberists",
            "choices-2-votes": "500",
            "choices-2-ORDER": "0",
            "choices-2-DELETE": "",
            "choices-3-choice": "",
            "choices-3-votes": "",
            "choices-3-ORDER": "",
            "choices-3-DELETE": "",
        }
        formset = ChoiceFormSet(data, auto_id=False, prefix="choices")
        self.assertTrue(formset.is_valid())
        self.assertEqual(
            [form.cleaned_data for form in formset.ordered_forms],
            [
                {
                    "votes": 500,
                    "DELETE": False,
                    "ORDER": 0,
                    "choice": "The Decemberists",
                },
                {"votes": 100, "DELETE": False, "ORDER": 1, "choice": "Calexico"},
            ],
        )
        self.assertEqual(
            [form.cleaned_data for form in formset.deleted_forms],
            [{"votes": 900, "DELETE": True, "ORDER": 2, "choice": "Fergie"}],
        )