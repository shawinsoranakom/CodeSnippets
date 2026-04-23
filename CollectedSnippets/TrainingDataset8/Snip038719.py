def _get_metadata(self):
        """Returns the metadata for the most recent element in the
        DeltaGenerator queue
        """
        return self.forward_msg_queue._queue[-1].metadata