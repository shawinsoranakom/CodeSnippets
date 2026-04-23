def normalize_name(self, name):
        """
        Get the properly shortened and uppercased identifier as returned by
        quote_name() but without the quotes.
        """
        nn = self.quote_name(name)
        if nn[0] == '"' and nn[-1] == '"':
            nn = nn[1:-1]
        return nn