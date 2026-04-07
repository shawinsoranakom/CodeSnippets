def __len__(self):
        "Return the number of rings in this Polygon."
        return self.num_interior_rings + 1