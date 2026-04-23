def test_no_default_database(self):
        DATABASES = {"other": {}}
        conns = ConnectionHandler(DATABASES)
        msg = "You must define a 'default' database."
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            conns["other"].ensure_connection()