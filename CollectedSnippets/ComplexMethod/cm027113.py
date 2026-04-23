def _filter_unique_constraint_integrity_error(err: Exception) -> bool:
        """Handle unique constraint integrity errors."""
        if not isinstance(err, StatementError):
            return False

        assert instance.engine is not None
        dialect_name = instance.engine.dialect.name

        ignore = False
        if (
            dialect_name == SupportedDialect.SQLITE
            and "UNIQUE constraint failed" in str(err)
        ):
            ignore = True
        if (
            dialect_name == SupportedDialect.POSTGRESQL
            and err.orig
            and hasattr(err.orig, "pgcode")
            and err.orig.pgcode == "23505"
        ):
            ignore = True
        if (
            dialect_name == SupportedDialect.MYSQL
            and err.orig
            and hasattr(err.orig, "args")
        ):
            with contextlib.suppress(TypeError):
                if err.orig.args[0] == 1062:
                    ignore = True

        if ignore:
            _LOGGER.warning(
                "Blocked attempt to insert duplicated %s rows, please report at %s",
                row_type,
                "https://github.com/home-assistant/core/issues?q=is%3Aopen+is%3Aissue+label%3A%22integration%3A+recorder%22",
                exc_info=err,
            )

        return ignore