def test_as_table(self):
        self.assertHTMLEqual(
            self.formset.as_table(),
            self.management_form_html
            + (
                "<tr><th>Choice:</th><td>"
                '<input type="text" name="choices-0-choice" value="Calexico"></td></tr>'
                "<tr><th>Votes:</th><td>"
                '<input type="number" name="choices-0-votes" value="100"></td></tr>'
            ),
        )