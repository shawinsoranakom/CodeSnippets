def test_as_p(self):
        self.assertHTMLEqual(
            self.formset.as_p(),
            self.management_form_html
            + (
                "<p>Choice: "
                '<input type="text" name="choices-0-choice" value="Calexico"></p>'
                '<p>Votes: <input type="number" name="choices-0-votes" value="100"></p>'
            ),
        )