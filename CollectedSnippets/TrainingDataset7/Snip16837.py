def test_attrs(self):
        w = widgets.AdminDateWidget()
        self.assertHTMLEqual(
            w.render("test", datetime(2007, 12, 1, 9, 30)),
            '<p class="date">'
            '<input aria-describedby="id_test_timezone_warning_helptext" '
            'value="2007-12-01" type="text" class="vDateField" name="test" '
            'size="10"></p>',
        )
        # pass attrs to widget
        w = widgets.AdminDateWidget(attrs={"size": 20, "class": "myDateField"})
        self.assertHTMLEqual(
            w.render("test", datetime(2007, 12, 1, 9, 30)),
            '<p class="date">'
            '<input aria-describedby="id_test_timezone_warning_helptext" '
            'value="2007-12-01" type="text" class="myDateField" name="test" '
            'size="20"></p>',
        )