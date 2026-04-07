def __deepcopy__(self, memo):
        """Limit the amount of work when a Query is deepcopied."""
        result = self.clone()
        memo[id(self)] = result
        return result