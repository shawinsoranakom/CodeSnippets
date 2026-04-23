def wkt(self):
        "Return the WKT (Well-Known Text) representation of this Geometry."
        return wkt_w(dim=3 if self.hasz else 2, trim=True).write(self).decode()