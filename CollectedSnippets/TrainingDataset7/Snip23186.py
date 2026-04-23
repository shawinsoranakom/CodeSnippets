def test_save_empty_label_forms(self):
        # Saving a form with a blank choice results in the expected
        # value being stored in the database.
        tests = [
            (EmptyCharLabelNoneChoiceForm, "choice_string_w_none", None),
            (EmptyIntegerLabelChoiceForm, "choice_integer", None),
            (EmptyCharLabelChoiceForm, "choice", ""),
        ]

        for form, key, expected in tests:
            with self.subTest(form=form):
                f = form({"name": "some-key", key: ""})
                self.assertTrue(f.is_valid())
                m = f.save()
                self.assertEqual(expected, getattr(m, key))
                self.assertEqual(
                    "No Preference", getattr(m, "get_{}_display".format(key))()
                )