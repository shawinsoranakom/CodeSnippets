def get_connection():
    new_connection = connection.copy()
    yield new_connection
    new_connection.close()