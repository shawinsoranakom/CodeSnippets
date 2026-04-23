def test_hidden_initial_gets_id(self):
        class MyForm(Form):
            field1 = CharField(max_length=50, show_hidden_initial=True)

        self.assertHTMLEqual(
            MyForm().as_table(),
            '<tr><th><label for="id_field1">Field1:</label></th><td>'
            '<input id="id_field1" type="text" name="field1" maxlength="50" required>'
            '<input type="hidden" name="initial-field1" id="initial-id_field1">'
            "</td></tr>",
        )