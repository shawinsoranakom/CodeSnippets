def set_matricies(self, red=None, green=None, blue=None, red_edge=None, nir=None):
    if red is not None:
        self.red = red
    if green is not None:
        self.green = green
    if blue is not None:
        self.blue = blue
    if red_edge is not None:
        self.redEdge = red_edge
    if nir is not None:
        self.nir = nir
    return True
