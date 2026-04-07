def get_count(self, using):
        """
        Perform a COUNT() query using the current filter constraints.
        """
        obj = self.clone()
        return obj.get_aggregation(using, {"__count": Count("*")})["__count"]