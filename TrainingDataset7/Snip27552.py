def setUp(self):
        self.prompt = OutputWrapper(StringIO())
        self.questioner = InteractiveMigrationQuestioner(prompt_output=self.prompt)