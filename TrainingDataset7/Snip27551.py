def test_ask_not_null_alteration_not_provided(self, mock):
        questioner = InteractiveMigrationQuestioner(
            prompt_output=OutputWrapper(StringIO())
        )
        question = questioner.ask_not_null_alteration("field_name", "model_name")
        self.assertEqual(question, NOT_PROVIDED)