def test_as_div(self):
        self.assertHTMLEqual(
            self.formset.as_div(),
            self.management_form_html
            + (
                "<div>Choice: "
                '<input type="text" name="choices-0-choice" value="Calexico"></div>'
                '<div>Votes: <input type="number" name="choices-0-votes" value="100">'
                "</div>"
            ),
        )