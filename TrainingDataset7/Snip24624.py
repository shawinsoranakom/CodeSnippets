def test_get_context_attrs(self):
        # The Widget.get_context() attrs argument overrides self.attrs.
        widget = BaseGeometryWidget(attrs={"geom_type": "POINT"})
        context = widget.get_context("point", None, attrs={"geom_type": "POINT2"})
        self.assertEqual(context["widget"]["attrs"]["geom_type"], "POINT2")
        # Widget.get_context() returns expected name for geom_type.
        widget = BaseGeometryWidget(attrs={"geom_type": "POLYGON"})
        context = widget.get_context("polygon", None, None)
        self.assertEqual(context["widget"]["attrs"]["geom_name"], "Polygon")
        # Widget.get_context() returns 'Geometry' instead of 'Unknown'.
        widget = BaseGeometryWidget(attrs={"geom_type": "GEOMETRY"})
        context = widget.get_context("geometry", None, None)
        self.assertEqual(context["widget"]["attrs"]["geom_name"], "Geometry")