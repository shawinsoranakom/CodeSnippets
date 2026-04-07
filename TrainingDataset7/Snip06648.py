def get_new_connection(self, conn_params):
        connection = super().get_new_connection(conn_params)
        if is_psycopg3:
            self.register_geometry_adapters(connection)
        return connection