def __next__(self):
        for event, node in self.event_stream:
            if event == "START_ELEMENT" and node.nodeName == "object":
                with fast_cache_clearing():
                    self.event_stream.expandNode(node)
                return self._handle_object(node)
        raise StopIteration