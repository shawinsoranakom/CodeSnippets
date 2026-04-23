def optimize(self, operations, app_label):
        """
        Handy shortcut for getting results + number of loops
        """
        optimizer = MigrationOptimizer()
        return optimizer.optimize(operations, app_label), optimizer._iterations