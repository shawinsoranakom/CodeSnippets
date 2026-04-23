def explain_query_prefix(self, format=None, **options):
        # Alias MySQL's TRADITIONAL to TEXT for consistency with other
        # backends.
        if format and format.upper() == "TEXT":
            format = "TRADITIONAL"
        elif (
            not format and "TREE" in self.connection.features.supported_explain_formats
        ):
            # Use TREE by default (if supported) as it's more informative.
            format = "TREE"
        analyze = options.pop("analyze", False)
        prefix = super().explain_query_prefix(format, **options)
        if analyze:
            # MariaDB uses ANALYZE instead of EXPLAIN ANALYZE.
            prefix = (
                "ANALYZE" if self.connection.mysql_is_mariadb else prefix + " ANALYZE"
            )
        if format and not (analyze and not self.connection.mysql_is_mariadb):
            # Only MariaDB supports the analyze option with formats.
            prefix += " FORMAT=%s" % format
        return prefix