def __init__(self, failfast=False, resultclass=None, buffer=False):
        self.failfast = failfast
        self.buffer = buffer
        if resultclass is not None:
            self.resultclass = resultclass