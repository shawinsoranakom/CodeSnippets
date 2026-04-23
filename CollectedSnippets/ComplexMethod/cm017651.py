def format(self, record):
        if (alias := getattr(record, "alias", None)) in connections:
            format_sql = connections[alias].ops.format_debug_sql

            sql = None
            formatted_sql = None
            if args := record.args:
                if isinstance(args, tuple) and len(args) > 1 and (sql := args[1]):
                    record.args = (args[0], formatted_sql := format_sql(sql), *args[2:])
                elif isinstance(record.args, dict) and (sql := record.args.get("sql")):
                    record.args["sql"] = formatted_sql = format_sql(sql)

            if extra_sql := getattr(record, "sql", None):
                if extra_sql == sql:
                    record.sql = formatted_sql
                else:
                    record.sql = format_sql(extra_sql)

        return super().format(record)