def test_field_string_value(self):
        """
        Initialization of a geometry field with a valid/empty/invalid string.
        Only the invalid string should trigger an error log entry.
        """

        class PointForm(forms.Form):
            pt1 = forms.PointField(srid=4326)
            pt2 = forms.PointField(srid=4326)
            pt3 = forms.PointField(srid=4326)

        form = PointForm(
            {
                "pt1": "SRID=4326;POINT(7.3 44)",  # valid
                "pt2": "",  # empty
                "pt3": "PNT(0)",  # invalid
            }
        )

        with self.assertLogs("django.contrib.gis", "ERROR") as logger_calls:
            output = str(form)

        # The first point can't use assertInHTML() due to non-deterministic
        # ordering of the rendered dictionary.
        pt1_serialized = re.search(r"<textarea [^>]*>({[^<]+})<", output)[1]
        pt1_json = pt1_serialized.replace("&quot;", '"')
        pt1_expected = GEOSGeometry(form.data["pt1"]).transform(3857, clone=True)
        self.assertJSONEqual(pt1_json, pt1_expected.json)

        self.assertInHTML(
            '<textarea id="id_pt2" class="vSerializedField required" cols="150"'
            ' rows="10" name="pt2" hidden></textarea>',
            output,
        )
        self.assertInHTML(
            '<textarea id="id_pt3" class="vSerializedField required" cols="150"'
            ' rows="10" name="pt3" hidden></textarea>',
            output,
        )
        # Only the invalid PNT(0) triggers an error log entry.
        # Deserialization is called in form clean and in widget rendering.
        self.assertEqual(len(logger_calls.records), 2)
        self.assertEqual(
            logger_calls.records[0].getMessage(),
            "Error creating geometry from value 'PNT(0)' (String input "
            "unrecognized as WKT EWKT, and HEXEWKB.)",
        )