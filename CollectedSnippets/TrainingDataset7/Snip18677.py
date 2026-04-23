def test_connect_pool_setting_ignored_for_psycopg2(self):
        new_connection = no_pool_connection()
        new_connection.settings_dict["OPTIONS"]["pool"] = True
        msg = "Database pooling requires psycopg >= 3"
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            new_connection.connect()