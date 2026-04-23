def year_lookup_bounds(self, connection, year):
        from django.db.models.functions import ExtractIsoYear

        iso_year = isinstance(self.lhs, ExtractIsoYear)
        output_field = self.lhs.lhs.output_field
        if isinstance(output_field, DateTimeField):
            bounds = connection.ops.year_lookup_bounds_for_datetime_field(
                year,
                iso_year=iso_year,
            )
        else:
            bounds = connection.ops.year_lookup_bounds_for_date_field(
                year,
                iso_year=iso_year,
            )
        return bounds