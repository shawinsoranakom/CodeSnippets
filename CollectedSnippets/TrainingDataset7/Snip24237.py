def test_kmz(self):
        "Testing `render_to_kmz` with non-ASCII data. See #11624."
        name = "Åland Islands"
        places = [
            {
                "name": name,
                "description": name,
                "kml": "<Point><coordinates>5.0,23.0</coordinates></Point>",
            }
        ]
        render_to_kmz("gis/kml/placemarks.kml", {"places": places})