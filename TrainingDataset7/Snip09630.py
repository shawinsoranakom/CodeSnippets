def __init__(self, connection, database):
        self.cursor = connection.cursor()
        self.cursor.outputtypehandler = self._output_type_handler
        self.database = database