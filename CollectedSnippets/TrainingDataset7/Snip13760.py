def run(self, test):
        result = self.resultclass()
        unittest.registerResult(result)
        result.failfast = self.failfast
        result.buffer = self.buffer
        test(result)
        return result