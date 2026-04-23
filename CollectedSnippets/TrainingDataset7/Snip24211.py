def test_make_valid_output_field(self):
        # output_field is GeometryField instance because different geometry
        # types can be returned.
        output_field = functions.MakeValid(
            Value(Polygon(), PolygonField(srid=42)),
        ).output_field
        self.assertIs(output_field.__class__, GeometryField)
        self.assertEqual(output_field.srid, 42)