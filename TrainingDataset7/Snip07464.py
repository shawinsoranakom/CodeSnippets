def outdim(self, new_dim):
        if new_dim not in (2, 3):
            raise ValueError("WKT output dimension must be 2 or 3")
        wkt_writer_set_outdim(self.ptr, new_dim)