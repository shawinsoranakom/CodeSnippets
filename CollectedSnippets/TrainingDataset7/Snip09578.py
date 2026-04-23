def lookup_cast(self, lookup_type, internal_type=None):
        lookup = "%s"
        if internal_type == "JSONField":
            if self.connection.mysql_is_mariadb or lookup_type in (
                "iexact",
                "contains",
                "icontains",
                "startswith",
                "istartswith",
                "endswith",
                "iendswith",
                "regex",
                "iregex",
            ):
                lookup = "JSON_UNQUOTE(%s)"
        return lookup