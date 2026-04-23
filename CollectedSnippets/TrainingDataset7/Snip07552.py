def check_ogr_fld(ogr_map_fld):
            try:
                idx = ogr_fields.index(ogr_map_fld)
            except ValueError:
                raise LayerMapError(
                    'Given mapping OGR field "%s" not found in OGR Layer.' % ogr_map_fld
                )
            return idx