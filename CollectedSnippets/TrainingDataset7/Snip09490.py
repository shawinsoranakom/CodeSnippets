def get_new_connection(self, conn_params):
        connection = Database.connect(**conn_params)
        return connection