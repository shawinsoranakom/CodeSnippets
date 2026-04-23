def test_attrs(self):
        w = widgets.AdminTimeWidget()
        self.assertHTMLEqual(
            w.render("test", datetime(2007, 12, 1, 9, 30)),
            '<p class="time">'
            '<input aria-describedby="id_test_timezone_warning_helptext" '
            'value="09:30:00" type="text" class="vTimeField" name="test" '
            'size="8"></p>',
        )
        # pass attrs to widget
        w = widgets.AdminTimeWidget(attrs={"size": 20, "class": "myTimeField"})
        self.assertHTMLEqual(
            w.render("test", datetime(2007, 12, 1, 9, 30)),
            '<p class="time">'
            '<input aria-describedby="id_test_timezone_warning_helptext" '
            'value="09:30:00" type="text" class="myTimeField" name="test" '
            'size="20"></p>',
        )