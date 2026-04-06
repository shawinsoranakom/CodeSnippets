def stderr(self):
        logs.warn('`stderr` is deprecated, please use `output` instead')
        return self.output