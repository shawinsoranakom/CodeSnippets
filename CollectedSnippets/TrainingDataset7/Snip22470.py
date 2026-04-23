def test_field_deepcopies_widget_instance(self):
        class CustomChoiceField(ChoiceField):
            widget = Select(attrs={"class": "my-custom-class"})

        class TestForm(Form):
            field1 = CustomChoiceField(choices=[])
            field2 = CustomChoiceField(choices=[])

        f = TestForm()
        f.fields["field1"].choices = [("1", "1")]
        f.fields["field2"].choices = [("2", "2")]
        self.assertEqual(f.fields["field1"].widget.choices, [("1", "1")])
        self.assertEqual(f.fields["field2"].widget.choices, [("2", "2")])