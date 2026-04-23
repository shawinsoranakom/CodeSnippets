def test_as_widget_custom_aria_describedby(self):
        class FoodForm(Form):
            intl_name = CharField(help_text="The food's international name.")

        form = FoodForm({"intl_name": "Rendang"})
        self.assertHTMLEqual(
            form["intl_name"].as_widget(attrs={"aria-describedby": "some_custom_id"}),
            '<input type="text" name="intl_name" value="Rendang"'
            'aria-describedby="some_custom_id" required id="id_intl_name">',
        )