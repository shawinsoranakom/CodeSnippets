def point_count(self):
        "Return the number of Points in this Polygon."
        # Summing up the number of points in each ring of the Polygon.
        return sum(self[i].point_count for i in range(self.geom_count))