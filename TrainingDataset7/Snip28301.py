def test_custom_choice_iterator_passes_model_to_widget(self):
        class CustomModelChoiceValue:
            def __init__(self, value, obj):
                self.value = value
                self.obj = obj

            def __str__(self):
                return str(self.value)

        class CustomModelChoiceIterator(ModelChoiceIterator):
            def choice(self, obj):
                value, label = super().choice(obj)
                return CustomModelChoiceValue(value, obj), label

        class CustomCheckboxSelectMultiple(CheckboxSelectMultiple):
            def create_option(
                self, name, value, label, selected, index, subindex=None, attrs=None
            ):
                option = super().create_option(
                    name, value, label, selected, index, subindex, attrs
                )
                # Modify the HTML based on the object being rendered.
                c = value.obj
                option["attrs"]["data-slug"] = c.slug
                return option

        class CustomModelMultipleChoiceField(forms.ModelMultipleChoiceField):
            iterator = CustomModelChoiceIterator
            widget = CustomCheckboxSelectMultiple

        field = CustomModelMultipleChoiceField(Category.objects.order_by("pk"))
        self.assertHTMLEqual(
            field.widget.render("name", []),
            """
            <div><div>
            <label><input type="checkbox" name="name" value="%s"
                data-slug="entertainment">Entertainment
            </label></div>
            <div><label>
            <input type="checkbox" name="name" value="%s" data-slug="test">A test
            </label></div>
            <div><label>
            <input type="checkbox" name="name" value="%s" data-slug="third-test">Third
            </label></div></div>
            """ % (self.c1.pk, self.c2.pk, self.c3.pk),
        )