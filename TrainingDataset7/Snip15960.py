def test_list_display_for_value_boolean(self):
        self.assertEqual(
            display_for_value(True, "", boolean=True),
            '<img src="/static/admin/img/icon-yes.svg" alt="True">',
        )
        self.assertEqual(
            display_for_value(False, "", boolean=True),
            '<img src="/static/admin/img/icon-no.svg" alt="False">',
        )
        self.assertEqual(display_for_value(True, ""), "True")
        self.assertEqual(display_for_value(False, ""), "False")