def lookup_cast(self, lookup_type, internal_type=None):
        if lookup_type in ("iexact", "icontains", "istartswith", "iendswith"):
            return "UPPER(%s)"
        if lookup_type != "isnull" and internal_type in (
            "BinaryField",
            "TextField",
        ):
            return "DBMS_LOB.SUBSTR(%s)"
        return "%s"