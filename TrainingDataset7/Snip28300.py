def test_choice_iterator_passes_model_to_widget(self):
        class CustomCheckboxSelectMultiple(CheckboxSelectMultiple):
            def create_option(
                self, name, value, label, selected, index, subindex=None, attrs=None
            ):
                option = super().create_option(
                    name, value, label, selected, index, subindex, attrs
                )
                # Modify the HTML based on the object being rendered.
                c = value.instance
                option["attrs"]["data-slug"] = c.slug
                return option

        class CustomModelMultipleChoiceField(forms.ModelMultipleChoiceField):
            widget = CustomCheckboxSelectMultiple

        field = CustomModelMultipleChoiceField(Category.objects.order_by("pk"))
        self.assertHTMLEqual(
            field.widget.render("name", []),
            (
                "<div>"
                '<div><label><input type="checkbox" name="name" value="%s" '
                'data-slug="entertainment">Entertainment</label></div>'
                '<div><label><input type="checkbox" name="name" value="%s" '
                'data-slug="test">A test</label></div>'
                '<div><label><input type="checkbox" name="name" value="%s" '
                'data-slug="third-test">Third</label></div>'
                "</div>"
            )
            % (self.c1.pk, self.c2.pk, self.c3.pk),
        )