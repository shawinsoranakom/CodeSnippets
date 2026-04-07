def tearDownConnectionTest(cls):
        cls.conn.settings_dict["CONN_MAX_AGE"] = cls.old_conn_max_age