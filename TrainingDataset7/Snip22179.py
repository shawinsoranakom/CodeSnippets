def test_loaddata_null_characters_on_postgresql(self):
        error, msg = connection.features.prohibits_null_characters_in_text_exception
        msg = f"Could not load fixtures.Article(pk=2): {msg}"
        with self.assertRaisesMessage(error, msg):
            management.call_command("loaddata", "null_character_in_field_value.json")