def _get_database_create_suffix(self, encoding=None, template=None):
        suffix = ""
        if encoding:
            suffix += " ENCODING '{}'".format(encoding)
        if template:
            suffix += " TEMPLATE {}".format(self._quote_name(template))
        return suffix and "WITH" + suffix