def change_transaction_mode(self, transaction_mode):
        new_connection = connection.copy()
        new_connection.settings_dict["OPTIONS"] = {
            **new_connection.settings_dict["OPTIONS"],
            "transaction_mode": transaction_mode,
        }
        try:
            yield new_connection
        finally:
            new_connection._close()