def do_log(self, msg, *logger_args, alias=DEFAULT_DB_ALIAS, extra=None):
        if extra is None:
            extra = {}
        if alias and "alias" not in extra:
            extra["alias"] = alias
        # Patch connection's format_debug_sql to ensure it was properly called.
        with mock.patch.object(
            connections[alias].ops, "format_debug_sql", side_effect=self.new_format_sql
        ):
            logger.info(msg, *logger_args, extra=extra)