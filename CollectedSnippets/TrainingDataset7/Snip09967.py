def convert_query(self, query, *, param_names=None):
        if param_names is None:
            # Convert from "format" style to "qmark" style.
            return FORMAT_QMARK_REGEX.sub("?", query).replace("%%", "%")
        else:
            # Convert from "pyformat" style to "named" style.
            return query % {name: f":{name}" for name in param_names}