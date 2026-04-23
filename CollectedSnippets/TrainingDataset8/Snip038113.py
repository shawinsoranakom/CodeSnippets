def flush_browser_queue(self) -> List[ForwardMsg]:
        """Clear our browser queue and return the messages it contained.

        The Server calls this periodically to deliver new messages
        to the browser associated with this session.

        Returns
        -------
        list[ForwardMsg]
            The messages that were removed from the queue and should
            be delivered to the browser.

        """
        return self._browser_queue.flush()