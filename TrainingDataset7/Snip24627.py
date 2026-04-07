def test_custom_serialization_widget(self):
        class CustomGeometryWidget(forms.BaseGeometryWidget):
            template_name = "gis/openlayers.html"
            deserialize_called = 0

            def serialize(self, value):
                return value.json if value else ""

            def deserialize(self, value):
                self.deserialize_called += 1
                return GEOSGeometry(value)

        class PointForm(forms.Form):
            p = forms.PointField(widget=CustomGeometryWidget)

        point = GEOSGeometry("SRID=4326;POINT(9.052734375 42.451171875)")
        form = PointForm(data={"p": point})
        self.assertIn(escape(point.json), form.as_p())

        CustomGeometryWidget.called = 0
        widget = form.fields["p"].widget
        # Force deserialize use due to a string value
        self.assertIn(escape(point.json), widget.render("p", point.json))
        self.assertEqual(widget.deserialize_called, 1)

        form = PointForm(data={"p": point.json})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["p"].srid, 4326)