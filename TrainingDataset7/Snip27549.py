def test_ask_initial_with_disabled_migrations(self):
        questioner = MigrationQuestioner()
        self.assertIs(False, questioner.ask_initial("migrations"))