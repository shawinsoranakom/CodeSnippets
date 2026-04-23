def wkt(self):
        "Return WKT representing a Polygon for this envelope."
        # TODO: Fix significant figures.
        return "POLYGON((%s %s,%s %s,%s %s,%s %s,%s %s))" % (
            self.min_x,
            self.min_y,
            self.min_x,
            self.max_y,
            self.max_x,
            self.max_y,
            self.max_x,
            self.min_y,
            self.min_x,
            self.min_y,
        )