def test_render(self):
        w = widgets.AdminSplitDateTime()
        self.assertHTMLEqual(
            w.render("test", datetime(2007, 12, 1, 9, 30), attrs={"id": "id_test"}),
            '<p class="datetime">'
            '<label for="id_test_0">Date:</label> '
            '<input aria-describedby="id_test_timezone_warning_helptext" '
            'value="2007-12-01" type="text" class="vDateField" '
            'name="test_0" size="10" id="id_test_0"><br>'
            '<label for="id_test_1">Time:</label> '
            '<input aria-describedby="id_test_timezone_warning_helptext" '
            'value="09:30:00" type="text" class="vTimeField" '
            'name="test_1" size="8" id="id_test_1"></p>',
        )