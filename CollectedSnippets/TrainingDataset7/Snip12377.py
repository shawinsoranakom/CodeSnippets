def __init__(self, using, savepoint, durable):
        self.using = using
        self.savepoint = savepoint
        self.durable = durable
        self._from_testcase = False