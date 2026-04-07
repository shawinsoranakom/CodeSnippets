def time_extract_sql(self, lookup_type, sql, params):
        if lookup_type == "second":
            # Truncate fractional seconds.
            return f"FLOOR(EXTRACT(SECOND FROM {sql}))", params
        return self.date_extract_sql(lookup_type, sql, params)