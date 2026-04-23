def add_field(self, model, field):
        super().add_field(model, field)
        self.run_geometry_sql()