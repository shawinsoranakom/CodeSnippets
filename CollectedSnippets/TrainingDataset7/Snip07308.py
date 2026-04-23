def kml(self):
        "Return the KML representation of this Geometry."
        gtype = self.geom_type
        return "<%s>%s</%s>" % (gtype, self.coord_seq.kml, gtype)