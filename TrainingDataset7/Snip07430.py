def kml(self):
        "Return the KML representation of this Polygon."
        inner_kml = "".join(
            "<innerBoundaryIs>%s</innerBoundaryIs>" % self[i + 1].kml
            for i in range(self.num_interior_rings)
        )
        return "<Polygon><outerBoundaryIs>%s</outerBoundaryIs>%s</Polygon>" % (
            self[0].kml,
            inner_kml,
        )