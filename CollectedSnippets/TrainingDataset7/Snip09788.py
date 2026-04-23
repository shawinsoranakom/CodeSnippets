def _configure_role(self, connection):
        if new_role := self.settings_dict["OPTIONS"].get("assume_role"):
            with connection.cursor() as cursor:
                sql = self.ops.compose_sql("SET ROLE %s", [new_role])
                cursor.execute(sql)
            return True
        return False