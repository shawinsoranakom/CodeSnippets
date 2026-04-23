def source_is_geography(self):
        return self.geo_field.geography and self.geo_field.srid == 4326