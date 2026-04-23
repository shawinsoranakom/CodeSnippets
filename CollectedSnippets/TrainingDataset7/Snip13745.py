def startTestRun(self):
        super().startTestRun()
        self.events.append(("startTestRun",))