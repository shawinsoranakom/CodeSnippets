def test_multipolygonfield(self):
        class PolygonForm(forms.Form):
            p = forms.MultiPolygonField()

        geom = self.geometries["multipolygon"]
        form = PolygonForm(data={"p": geom})
        self.assertTextarea(geom, form.as_p())
        self.assertMapWidget(form, "MultiPolygon")
        self.assertFalse(PolygonForm().is_valid())

        for invalid in [
            geo for key, geo in self.geometries.items() if key != "multipolygon"
        ]:
            self.assertFalse(PolygonForm(data={"p": invalid.wkt}).is_valid())