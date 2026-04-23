def upgrade(self, obj, format):
            # Dump ranges containing naive datetimes as tstzrange, because
            # Django doesn't use tz-aware ones.
            dumper = super().upgrade(obj, format)
            if dumper is not self and dumper.oid == TSRANGE_OID:
                dumper.oid = TSTZRANGE_OID
            return dumper