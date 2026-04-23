def point_count(self):
        "Return the number of Points in this Geometry Collection."
        # Summing up the number of points in each geometry in this collection
        return sum(self[i].point_count for i in range(self.geom_count))