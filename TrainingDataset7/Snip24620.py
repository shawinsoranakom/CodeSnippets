def test_geometrycollectionfield(self):
        class GeometryForm(forms.Form):
            g = forms.GeometryCollectionField()

        geom = self.geometries["geometrycollection"]
        form = GeometryForm(data={"g": geom})
        self.assertTextarea(geom, form.as_p())
        self.assertMapWidget(form, "GeometryCollection")
        self.assertFalse(GeometryForm().is_valid())

        for invalid in [
            geo for key, geo in self.geometries.items() if key != "geometrycollection"
        ]:
            self.assertFalse(GeometryForm(data={"g": invalid.wkt}).is_valid())