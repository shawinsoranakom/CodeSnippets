def get_geoms(lst, srid=None):
            return [GEOSGeometry(tg.wkt, srid) for tg in lst]