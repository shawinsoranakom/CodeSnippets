def test_widget_invalid_string(self):
        geoadmin = self.admin_site.get_model_admin(City)
        form = geoadmin.get_changelist_form(None)({"point": "INVALID()"})
        with self.assertLogs("django.contrib.gis", "ERROR") as cm:
            output = str(form["point"])
        self.assertInHTML(
            '<textarea id="id_point" class="vSerializedField required" cols="150"'
            ' rows="10" name="point" hidden></textarea>',
            output,
        )
        self.assertEqual(len(cm.records), 2)
        self.assertEqual(
            cm.records[0].getMessage(),
            "Error creating geometry from value 'INVALID()' (String input "
            "unrecognized as WKT EWKT, and HEXEWKB.)",
        )