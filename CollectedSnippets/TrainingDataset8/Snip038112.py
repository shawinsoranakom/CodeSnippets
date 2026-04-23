def clear_browser_queue(self) -> None:
        """Clear all pending ForwardMsgs from our browser queue."""
        self._browser_queue.clear()