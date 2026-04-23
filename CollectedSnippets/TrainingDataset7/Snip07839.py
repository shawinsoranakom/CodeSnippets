def quote_lexeme(value):
        adapter = adapt(psql_escape(value))
        adapter.encoding = "utf-8"
        return adapter.getquoted().decode()