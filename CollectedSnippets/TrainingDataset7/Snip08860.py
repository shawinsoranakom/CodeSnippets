def handle(self, **options):
        sql_statements = sql_flush(self.style, connections[options["database"]])
        if not sql_statements and options["verbosity"] >= 1:
            self.stderr.write("No tables found.")
        return "\n".join(sql_statements)