def as_sql(self, compiler, connection):
        if self.rhs is None:
            # Interpret __iexact=None on KeyTextTransform as __exact=None on
            # KeyTransform.
            keytransform = KeyTransform(self.lhs.key_name, self.lhs.lhs)
            exact_lookup = keytransform.get_lookup("exact")(keytransform, self.rhs)
            # Delegate to the backend vendor method, if it exists.
            vendor = connection.vendor
            as_vendor = getattr(exact_lookup, f"as_{vendor}", exact_lookup.as_sql)
            return as_vendor(compiler, connection)
        return super().as_sql(compiler, connection)