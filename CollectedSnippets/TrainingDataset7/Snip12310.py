def add_votes(self, votes):
        """
        Add single vote per item to self.votes. Parameter can be any
        iterable.
        """
        self.votes.update(votes)