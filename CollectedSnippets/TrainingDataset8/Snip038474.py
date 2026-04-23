def get_message_from_queue(self, index=-1) -> ForwardMsg:
        """Get a ForwardMsg proto from the queue, by index."""
        return self.forward_msg_queue._queue[index]