def test_sql_table_creation_suffix_with_encoding(self):
        settings = {"CHARSET": "UTF8"}
        self.check_sql_table_creation_suffix(settings, "WITH ENCODING 'UTF8'")