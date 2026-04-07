def create_model(self, model):
        super().create_model(model)
        # Create geometry columns
        for sql in self.geometry_sql:
            self.execute(sql)
        self.geometry_sql = []