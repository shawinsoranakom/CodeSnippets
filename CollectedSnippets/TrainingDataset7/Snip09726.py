def fetch_returned_rows(self, cursor, returning_params):
        return list(zip(*(param.get_value() for param in returning_params)))