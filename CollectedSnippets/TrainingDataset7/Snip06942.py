def from_json(geom_input):
        return OGRGeometry(OGRGeometry._from_json(force_bytes(geom_input)))