def sql_delete_check(self):
        if self.connection.mysql_is_mariadb:
            # The name of the column check constraint is the same as the field
            # name on MariaDB. Adding IF EXISTS clause prevents migrations
            # crash. Constraint is removed during a "MODIFY" column statement.
            return "ALTER TABLE %(table)s DROP CONSTRAINT IF EXISTS %(name)s"
        return "ALTER TABLE %(table)s DROP CHECK %(name)s"