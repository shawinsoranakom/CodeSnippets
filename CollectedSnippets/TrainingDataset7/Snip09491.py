def init_connection_state(self):
        super().init_connection_state()
        assignments = []
        if self.features.is_sql_auto_is_null_enabled:
            # SQL_AUTO_IS_NULL controls whether an AUTO_INCREMENT column on
            # a recently inserted row will return when the field is tested
            # for NULL. Disabling this brings this aspect of MySQL in line
            # with SQL standards.
            assignments.append("SET SQL_AUTO_IS_NULL = 0")

        if self.isolation_level:
            assignments.append(
                "SET SESSION TRANSACTION ISOLATION LEVEL %s"
                % self.isolation_level.upper()
            )

        if assignments:
            with self.cursor() as cursor:
                cursor.execute("; ".join(assignments))