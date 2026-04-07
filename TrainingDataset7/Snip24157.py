def test_widget_empty_string(self):
        geoadmin = self.admin_site.get_model_admin(City)
        form = geoadmin.get_changelist_form(None)({"point": ""})
        with self.assertRaisesMessage(AssertionError, "no logs"):
            with self.assertLogs("django.contrib.gis", "ERROR"):
                output = str(form["point"])
        self.assertInHTML(
            '<textarea id="id_point" class="vSerializedField required" cols="150"'
            ' rows="10" name="point" hidden></textarea>',
            output,
        )