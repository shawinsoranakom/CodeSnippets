def record_applied(self, recorder, app, name):
        recorder.record_applied(app, name)
        self.applied_records.append((recorder, app, name))