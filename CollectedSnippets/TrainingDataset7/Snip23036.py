def test_as_ul(self):
        self.assertHTMLEqual(
            self.formset.as_ul(),
            self.management_form_html
            + (
                "<li>Choice: "
                '<input type="text" name="choices-0-choice" value="Calexico"></li>'
                "<li>Votes: "
                '<input type="number" name="choices-0-votes" value="100"></li>'
            ),
        )