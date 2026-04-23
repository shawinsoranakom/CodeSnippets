def test_ask_not_null_alteration(self):
        questioner = MigrationQuestioner()
        self.assertIsNone(
            questioner.ask_not_null_alteration("field_name", "model_name")
        )