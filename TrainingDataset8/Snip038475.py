def get_delta_from_queue(self, index=-1) -> Delta:
        """Get a Delta proto from the queue, by index."""
        deltas = self.get_all_deltas_from_queue()
        return deltas[index]