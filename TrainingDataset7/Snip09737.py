def quote_name(self, name):
        # SQL92 requires delimited (quoted) names to be case-sensitive. When
        # not quoted, Oracle has case-insensitive behavior for identifiers, but
        # always defaults to uppercase.
        # We simplify things by making Oracle identifiers always uppercase.
        if not name.startswith('"') and not name.endswith('"'):
            name = '"%s"' % truncate_name(name, self.max_name_length())
        # Oracle puts the query text into a (query % args) construct, so %
        # signs in names need to be escaped. The '%%' will be collapsed back to
        # '%' at that stage so we aren't really making the name longer here.
        name = name.replace("%", "%%")
        return name.upper()