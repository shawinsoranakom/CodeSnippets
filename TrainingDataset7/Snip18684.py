def test_client_encoding_utf8_enforce(self):
        new_connection = no_pool_connection()
        new_connection.settings_dict["OPTIONS"]["client_encoding"] = "iso-8859-2"
        try:
            new_connection.connect()
            if is_psycopg3:
                self.assertEqual(new_connection.connection.info.encoding, "utf-8")
            else:
                self.assertEqual(new_connection.connection.encoding, "UTF8")
        finally:
            new_connection.close()