def upgrade(self, obj, format):
                if obj.is_geometry:
                    if obj.geography:
                        return self.GeographyDumper(GeographyType)
                    else:
                        return self.GeometryDumper(GeometryType)
                else:
                    return self.RasterDumper(RasterType)