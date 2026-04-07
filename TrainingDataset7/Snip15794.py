def setUp(self):
        self.stdout = StringIO()
        self.runserver_command = RunserverCommand(stdout=self.stdout)