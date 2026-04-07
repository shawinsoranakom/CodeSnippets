def __conform__(self, proto):
        """Does the given protocol conform to what Psycopg2 expects?"""
        from psycopg2.extensions import ISQLQuote

        if proto == ISQLQuote:
            return self
        else:
            raise Exception(
                "Error implementing psycopg2 protocol. Is psycopg2 installed?"
            )