def field_as_sql(self, field, get_placeholder_sql, val):
        """
        Take a field and a value intended to be saved on that field, and
        return placeholder SQL and accompanying params. Check for raw values,
        fields with get_placeholder_sql(), and compilable defined in that
        order.

        When field is None, consider the value raw and use it as the
        placeholder, with no corresponding parameters returned.
        """
        if field is None:
            # A field value of None means the value is raw.
            sql, params = val, []
        elif get_placeholder_sql is not None:
            # Some fields (e.g. geo fields) need special munging before
            # they can be inserted.
            sql, params = get_placeholder_sql(val, self, self.connection)
        elif hasattr(val, "as_sql"):
            # This is an expression, let's compile it.
            sql, params = self.compile(val)
        else:
            # Return the common case for the placeholder
            sql, params = "%s", [val]

        # The following hook is only used by Oracle Spatial, which sometimes
        # needs to yield 'NULL' and () as its placeholder and params instead
        # of '%s' and (None,). The 'NULL' placeholder is produced earlier by
        # OracleOperations.get_geom_placeholder(). The following line removes
        # the corresponding None parameter. See ticket #10888.
        params = self.connection.ops.modify_insert_params(sql, params)

        return sql, params