def kml(self):
        "Return the KML representation for the coordinates."
        if self.hasz:
            coords = [f"{coord[0]},{coord[1]},{coord[2]}" for coord in self]
        else:
            coords = [f"{coord[0]},{coord[1]},0" for coord in self]

        coordinate_string = " ".join(coords)
        return f"<coordinates>{coordinate_string}</coordinates>"