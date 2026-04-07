def test_null(self):
        "Testing GeometryField's handling of null (None) geometries."
        # Form fields, by default, are required (`required=True`)
        fld = forms.GeometryField()
        with self.assertRaisesMessage(ValidationError, "No geometry value provided."):
            fld.clean(None)

        # This will clean None as a geometry (See #10660).
        fld = forms.GeometryField(required=False)
        self.assertIsNone(fld.clean(None))