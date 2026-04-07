def test_form_custom_boundfield(self):
        class CustomBoundFieldPerson(Person):
            bound_field_class = BoundFieldWithTwoColons

        with self.subTest("form's BoundField takes over renderer's BoundField"):
            t = Template("{{ form }}")
            html = t.render(Context({"form": CustomBoundFieldPerson()}))
            expected = """
                <div><label for="id_first_name">First name::</label>
                <input type="text" name="first_name" required
                id="id_first_name"></div>
                <div><label for="id_last_name">Last name::</label>
                <input type="text" name="last_name" required
                id="id_last_name"></div><div>
                <label for="id_birthday">Birthday::</label>
                <input type="text" name="birthday" required
                id="id_birthday"></div>"""
            self.assertHTMLEqual(html, expected)

        with self.subTest("Constructor argument takes over class property"):
            t = Template("{{ form }}")
            html = t.render(
                Context(
                    {
                        "form": CustomBoundFieldPerson(
                            bound_field_class=BoundFieldWithCustomClass
                        )
                    }
                )
            )
            expected = """
                <div><label class="custom-class" for="id_first_name">First name:</label>
                <input type="text" name="first_name" required
                id="id_first_name"></div>
                <div><label class="custom-class" for="id_last_name">Last name:</label>
                <input type="text" name="last_name" required
                id="id_last_name"></div><div>
                <label class="custom-class" for="id_birthday">Birthday:</label>
                <input type="text" name="birthday" required
                id="id_birthday"></div>"""
            self.assertHTMLEqual(html, expected)

        with self.subTest("Overriding css_classes works as expected"):
            t = Template("{{ form }}")
            html = t.render(
                Context(
                    {
                        "form": CustomBoundFieldPerson(
                            bound_field_class=BoundFieldWithWrappingClass
                        )
                    }
                )
            )
            expected = """
                <div class="field-class"><label for="id_first_name">First name:</label>
                <input type="text" name="first_name" required
                id="id_first_name"></div>
                <div class="field-class"><label for="id_last_name">Last name:</label>
                <input type="text" name="last_name" required
                id="id_last_name"></div><div class="field-class">
                <label for="id_birthday">Birthday:</label>
                <input type="text" name="birthday" required
                id="id_birthday"></div>"""
            self.assertHTMLEqual(html, expected)