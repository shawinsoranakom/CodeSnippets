def db_type(self, connection):
        return connection.ops.geo_db_type(self)