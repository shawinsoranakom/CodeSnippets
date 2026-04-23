def supports_collation_on_charfield(self):
        sql = "SELECT CAST('a' AS VARCHAR2(4001))" + self.bare_select_suffix
        with self.connection.cursor() as cursor:
            try:
                cursor.execute(sql)
            except DatabaseError as e:
                if e.args[0].code == 910:
                    return False
                raise
            return True