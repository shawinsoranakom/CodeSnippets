def run_geometry_sql(self):
        for sql in self.geometry_sql:
            self.execute(sql)
        self.geometry_sql = []