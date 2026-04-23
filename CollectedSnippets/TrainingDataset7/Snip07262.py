def from_ewkt(ewkt):
        ewkt = force_bytes(ewkt)
        srid = None
        parts = ewkt.split(b";", 1)
        if len(parts) == 2:
            srid_part, wkt = parts
            match = re.match(rb"SRID=(?P<srid>\-?\d+)", srid_part)
            if not match:
                raise ValueError("EWKT has invalid SRID part.")
            srid = int(match["srid"])
        else:
            wkt = ewkt
        if not wkt:
            raise ValueError("Expected WKT but got an empty string.")
        return GEOSGeometry(GEOSGeometry._from_wkt(wkt), srid=srid)