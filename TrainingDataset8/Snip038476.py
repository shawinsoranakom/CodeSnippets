def get_all_deltas_from_queue(self) -> List[Delta]:
        """Return all the delta messages in our ForwardMsgQueue"""
        return [
            msg.delta for msg in self.forward_msg_queue._queue if msg.HasField("delta")
        ]