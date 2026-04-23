def test_sql_table_creation_suffix_with_encoding_and_template(self):
        settings = {"CHARSET": "UTF8", "TEMPLATE": "template0"}
        self.check_sql_table_creation_suffix(
            settings, '''WITH ENCODING 'UTF8' TEMPLATE "template0"'''
        )