def get_fields(self, field_name):
        """
        Return a list containing the given field name for every Feature
        in the Layer.
        """
        if field_name not in self.fields:
            raise GDALException("invalid field name: %s" % field_name)
        return [feat.get(field_name) for feat in self]