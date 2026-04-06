def stdout(self):
        logs.warn('`stdout` is deprecated, please use `output` instead')
        return self.output