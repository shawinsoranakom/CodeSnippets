def get_targets(self, fixture_name, ser_fmt, cmp_fmt):
        databases = [self.using, None]
        cmp_fmts = self.compression_formats if cmp_fmt is None else [cmp_fmt]
        ser_fmts = self.serialization_formats if ser_fmt is None else [ser_fmt]
        return {
            "%s.%s"
            % (
                fixture_name,
                ".".join([ext for ext in combo if ext]),
            )
            for combo in product(databases, ser_fmts, cmp_fmts)
        }