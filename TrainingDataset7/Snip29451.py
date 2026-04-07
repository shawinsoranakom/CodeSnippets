def check_default_text_search_config(self):
        if self.default_text_search_config != "pg_catalog.english":
            self.skipTest("The default text search config is not 'english'.")