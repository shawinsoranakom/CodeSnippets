def test_field_custom_bound_field(self):
        class BoundFieldWithTwoColonsCharField(CharField):
            bound_field_class = BoundFieldWithTwoColons

        class CustomFieldBoundFieldPerson(Person):
            bound_field_class = BoundField

            first_name = BoundFieldWithTwoColonsCharField()
            last_name = BoundFieldWithTwoColonsCharField(
                bound_field_class=BoundFieldWithCustomClass
            )

        html = Template("{{ form }}").render(
            Context({"form": CustomFieldBoundFieldPerson()})
        )
        expected = """
            <div><label for="id_first_name">First name::</label>
            <input type="text" name="first_name" required
            id="id_first_name"></div>
            <div><label class="custom-class" for="id_last_name">Last name:</label>
            <input type="text" name="last_name" required
            id="id_last_name"></div><div>
            <label for="id_birthday">Birthday:</label>
            <input type="text" name="birthday" required
            id="id_birthday"></div>"""
        self.assertHTMLEqual(html, expected)