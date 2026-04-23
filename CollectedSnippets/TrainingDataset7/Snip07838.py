def quote_lexeme(value):
        return UTF8Dumper(str).quote(psql_escape(value)).decode()