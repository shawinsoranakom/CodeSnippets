def db_parameters(self, connection):
        db_params = super().db_parameters(connection)
        db_params["collation"] = self.db_collation
        return db_params