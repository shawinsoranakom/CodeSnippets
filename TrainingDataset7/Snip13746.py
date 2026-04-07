def stopTestRun(self):
        super().stopTestRun()
        self.events.append(("stopTestRun",))