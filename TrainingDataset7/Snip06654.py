def get_key(self, obj, format):
                if obj.is_geometry:
                    return GeographyType if obj.geography else GeometryType
                else:
                    return RasterType