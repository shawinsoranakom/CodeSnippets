def test_sql_table_creation_suffix_with_template(self):
        settings = {"TEMPLATE": "template0"}
        self.check_sql_table_creation_suffix(settings, 'WITH TEMPLATE "template0"')