def test_cannot_open_new_connection_in_atomic_block(self):
        new_connection = no_pool_connection(alias="default_pool")
        new_connection.settings_dict["OPTIONS"]["pool"] = True
        msg = "Cannot open a new connection in an atomic block."
        new_connection.in_atomic_block = True
        new_connection.closed_in_transaction = True
        with self.assertRaisesMessage(ProgrammingError, msg):
            new_connection.ensure_connection()