def do_query(self, table, where, using):
        self.alias_map = {table: self.alias_map[table]}
        self.where = where
        return self.get_compiler(using).execute_sql(ROW_COUNT)