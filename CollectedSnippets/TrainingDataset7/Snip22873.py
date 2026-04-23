def test_label_does_not_include_new_line(self):
        form = Person()
        field = form["first_name"]
        self.assertEqual(
            field.label_tag(), '<label for="id_first_name">First name:</label>'
        )
        self.assertEqual(
            field.legend_tag(),
            "<legend>First name:</legend>",
        )