def flush_browser_queue(self) -> List[ForwardMsg]:
        """Clear the forward message queue and return the messages it contained.

        The Server calls this periodically to deliver new messages
        to the browser connected to this app.

        Returns
        -------
        list[ForwardMsg]
            The messages that were removed from the queue and should
            be delivered to the browser.

        """
        return self._session_data.flush_browser_queue()