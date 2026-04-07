def kml(self):
        "Return the KML for this Geometry Collection."
        return "<MultiGeometry>%s</MultiGeometry>" % "".join(g.kml for g in self)