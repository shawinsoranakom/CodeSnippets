def test_field_order(self):
        # A Form's fields are displayed in the same order in which they were
        # defined.
        class TestForm(Form):
            field1 = CharField()
            field2 = CharField()
            field3 = CharField()
            field4 = CharField()
            field5 = CharField()
            field6 = CharField()
            field7 = CharField()
            field8 = CharField()
            field9 = CharField()
            field10 = CharField()
            field11 = CharField()
            field12 = CharField()
            field13 = CharField()
            field14 = CharField()

        p = TestForm(auto_id=False)
        self.assertHTMLEqual(
            p.as_table(),
            "".join(
                f"<tr><th>Field{i}:</th><td>"
                f'<input type="text" name="field{i}" required></td></tr>'
                for i in range(1, 15)
            ),
        )