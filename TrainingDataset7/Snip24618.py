def test_polygonfield(self):
        class PolygonForm(forms.Form):
            p = forms.PolygonField()

        geom = self.geometries["polygon"]
        form = PolygonForm(data={"p": geom})
        self.assertTextarea(geom, form.as_p())
        self.assertMapWidget(form, "Polygon")
        self.assertFalse(PolygonForm().is_valid())

        for invalid in [
            geo for key, geo in self.geometries.items() if key != "polygon"
        ]:
            self.assertFalse(PolygonForm(data={"p": invalid.wkt}).is_valid())