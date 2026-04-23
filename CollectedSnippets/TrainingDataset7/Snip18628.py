def test_sql_table_creation_suffix_with_none_settings(self):
        settings = {"CHARSET": None, "TEMPLATE": None}
        self.check_sql_table_creation_suffix(settings, "")