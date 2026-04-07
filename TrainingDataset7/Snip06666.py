def check_geography(self, lookup, template_params):
        """Convert geography fields to geometry types, if necessary."""
        if lookup.lhs.output_field.geography and not self.geography:
            template_params["lhs"] += "::geometry"
        return template_params