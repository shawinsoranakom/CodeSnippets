def check_tables_exist(self, cr: Cursor) -> None:
        """
        Verify that all tables are present and try to initialize those that are missing.
        """
        from .environments import Environment  # noqa: PLC0415
        env = Environment(cr, SUPERUSER_ID, {})
        table2model = {
            model._table: name
            for name, model in env.registry.items()
            if not model._abstract and not model._table_query
        }
        missing_tables = set(table2model).difference(sql.existing_tables(cr, table2model))

        if missing_tables:
            missing = {table2model[table] for table in missing_tables}
            _logger.info("Models have no table: %s.", ", ".join(missing))
            # recreate missing tables
            for name in missing:
                _logger.info("Recreate table of model %s.", name)
                env[name].init()
            env.flush_all()
            # check again, and log errors if tables are still missing
            missing_tables = set(table2model).difference(sql.existing_tables(cr, table2model))
            for table in missing_tables:
                _logger.error("Model %s has no table.", table2model[table])