def is_finished(self):
        return self.status in {TaskResultStatus.FAILED, TaskResultStatus.SUCCESSFUL}