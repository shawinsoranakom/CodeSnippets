def assertDoesNotOptimize(self, operations, **kwargs):
        self.assertOptimizesTo(operations, operations, **kwargs)